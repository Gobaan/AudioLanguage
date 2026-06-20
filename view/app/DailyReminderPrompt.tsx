import { useState, type ChangeEvent } from 'react';
import { deleteReminderSubscription, fetchReminderPublicKey, saveReminderSubscription } from '../api/reminders';
import {
  DEFAULT_DAILY_REMINDER_TIME,
  canUsePushReminders,
  loadDailyReminderSettings,
  pushReminderUnavailableMessage,
  reminderPermission,
  reminderTimezone,
  registerReminderServiceWorker,
  requestReminderPermission,
  saveDailyReminderSettings,
  type DailyReminderSettings,
  type ReminderPermission,
  urlBase64ToUint8Array,
} from './dailyReminderNotifications';

type DailyReminderPromptProps = {
  participantId: string | null;
};

export function DailyReminderPrompt({ participantId }: DailyReminderPromptProps) {
  const [settings, setSettings] = useState<DailyReminderSettings>(() => loadDailyReminderSettings());
  const [permission, setPermission] = useState<ReminderPermission>(() => reminderPermission());
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const canNotify = permission !== 'unsupported' && canUsePushReminders() && participantId !== null;
  const isEnabled = settings.enabled && permission === 'granted';
  const statusText = reminderStatusText(settings, permission, isSaving, errorMessage);

  return (
    <section className="daily-reminder-prompt" aria-label="Daily reminder">
      <div>
        <span>Daily reminder</span>
        <h2>Practice at the same time each day</h2>
        <p>{statusText}</p>
      </div>
      <label>
        <span>Time</span>
        <input type="time" value={settings.time} onChange={updateReminderTime} />
      </label>
      <button type="button" onClick={isEnabled ? disableReminder : enableReminder} disabled={!canNotify || isSaving}>
        {isEnabled ? 'Turn off' : isSaving ? 'Saving...' : 'Notify me'}
      </button>
    </section>
  );

  function updateReminderTime(event: ChangeEvent<HTMLInputElement>) {
    const nextSettings = {
      ...settings,
      time: event.target.value || DEFAULT_DAILY_REMINDER_TIME,
    };
    setSettings(nextSettings);
    saveDailyReminderSettings(nextSettings);
    if (nextSettings.enabled && permission === 'granted') {
      void savePushSubscription(nextSettings);
    }
  }

  async function enableReminder() {
    if (!participantId || !canUsePushReminders()) {
      setPermission('unsupported');
      setErrorMessage(null);
      return;
    }

    setErrorMessage(null);
    const nextPermission = await requestReminderPermission();
    setPermission(nextPermission);
    if (nextPermission !== 'granted') {
      return;
    }

    const nextSettings = { ...settings, enabled: true };
    await savePushSubscription(nextSettings);
  }

  async function disableReminder() {
    const nextSettings = { ...settings, enabled: false };
    setSettings(nextSettings);
    saveDailyReminderSettings(nextSettings);
    setErrorMessage(null);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await deleteReminderSubscription(subscription.endpoint);
        await subscription.unsubscribe();
      }
    } catch (error) {
      setErrorMessage(reminderErrorMessage(error));
    }
  }

  async function savePushSubscription(nextSettings: DailyReminderSettings) {
    if (!participantId) {
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    try {
      const [{ publicKey }, registration] = await Promise.all([
        fetchReminderPublicKey(),
        registerReminderServiceWorker(),
      ]);
      const existingSubscription = await registration.pushManager.getSubscription();
      const subscription =
        existingSubscription ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        }));
      await saveReminderSubscription({
        participantId,
        time: nextSettings.time,
        timezone: reminderTimezone(),
        subscription: subscription.toJSON(),
      });
      setSettings(nextSettings);
      saveDailyReminderSettings(nextSettings);
    } catch (error) {
      setErrorMessage(reminderErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }
}

function reminderStatusText(
  settings: DailyReminderSettings,
  permission: ReminderPermission,
  isSaving: boolean,
  errorMessage: string | null,
): string {
  if (isSaving) {
    return 'Saving your reminder.';
  }
  if (errorMessage) {
    return errorMessage;
  }
  if (permission === 'unsupported' || !canUsePushReminders()) {
    return pushReminderUnavailableMessage();
  }
  if (settings.enabled && permission === 'granted') {
    return `Reminder set for ${formatReminderTime(settings.time)} local time. Turn it off here anytime.`;
  }
  if (permission === 'denied') {
    return 'Notifications are blocked in this browser.';
  }
  return `Default time: ${formatReminderTime(settings.time)}.`;
}

function reminderErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return 'Reminder setup failed. Try again.';
  }
  if (error.message.includes('Web Push dependencies')) {
    return 'Reminder server is missing Web Push dependencies. Run pip install -r requirements.txt.';
  }
  if (error.message.includes('ServiceWorker') || error.message.includes('service worker')) {
    return 'Reminder worker is unavailable. Rebuild and redeploy static assets.';
  }
  if (error.message.includes('push service error') || error.message.includes('Registration failed')) {
    return 'Browser push registration failed. Try Chrome, Edge, or Firefox with network access on HTTPS or localhost.';
  }
  return `Reminder setup failed: ${error.message}`;
}

function formatReminderTime(time: string): string {
  const [hoursText, minutes] = time.split(':');
  const hours = Number(hoursText);
  const period = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${minutes} ${period}`;
}
