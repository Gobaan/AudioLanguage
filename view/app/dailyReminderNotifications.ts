export const DEFAULT_DAILY_REMINDER_TIME = '22:00';
export const DAILY_REMINDER_STORAGE_KEY = 'audio-language-daily-reminder';

export type DailyReminderSettings = {
  enabled: boolean;
  time: string;
};

export type ReminderPermission = NotificationPermission | 'unsupported';

export function loadDailyReminderSettings(): DailyReminderSettings {
  if (typeof localStorage === 'undefined') {
    return defaultDailyReminderSettings();
  }

  try {
    const stored = localStorage.getItem(DAILY_REMINDER_STORAGE_KEY);
    if (!stored) {
      return defaultDailyReminderSettings();
    }
    const parsed = JSON.parse(stored) as Partial<DailyReminderSettings>;
    return {
      enabled: parsed.enabled === true,
      time: isReminderTime(parsed.time) ? parsed.time : DEFAULT_DAILY_REMINDER_TIME,
    };
  } catch {
    return defaultDailyReminderSettings();
  }
}

export function saveDailyReminderSettings(settings: DailyReminderSettings) {
  try {
    localStorage.setItem(DAILY_REMINDER_STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Reminder settings are convenience state; private browsing can reject storage.
  }
}

export function reminderPermission(): ReminderPermission {
  if (typeof Notification === 'undefined') {
    return 'unsupported';
  }
  return Notification.permission;
}

export async function requestReminderPermission(): Promise<ReminderPermission> {
  if (typeof Notification === 'undefined') {
    return 'unsupported';
  }
  return Notification.requestPermission();
}

export function reminderTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

export function canUsePushReminders(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    window.isSecureContext === true &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    typeof Notification !== 'undefined'
  );
}

export function pushReminderUnavailableMessage(): string {
  if (typeof window !== 'undefined' && window.isSecureContext === false) {
    return 'Use HTTPS or localhost to enable push reminders.';
  }
  return 'Push notifications are unavailable in this browser.';
}

export async function registerReminderServiceWorker(): Promise<ServiceWorkerRegistration> {
  await navigator.serviceWorker.register('/service-worker.js');
  return navigator.serviceWorker.ready;
}

export function urlBase64ToUint8Array(value: string): Uint8Array {
  const padding = '='.repeat((4 - (value.length % 4)) % 4);
  const base64 = `${value}${padding}`.replace(/-/g, '+').replace(/_/g, '/');
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map((char) => char.charCodeAt(0)));
}

function defaultDailyReminderSettings(): DailyReminderSettings {
  return {
    enabled: false,
    time: DEFAULT_DAILY_REMINDER_TIME,
  };
}

function isReminderTime(value: unknown): value is string {
  if (typeof value !== 'string' || !/^\d{2}:\d{2}$/.test(value)) {
    return false;
  }
  const [hours, minutes] = value.split(':').map(Number);
  return hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59;
}
