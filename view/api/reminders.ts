export type PushSubscriptionPayload = {
  endpoint?: string;
  expirationTime?: number | null;
  keys?: {
    p256dh?: string;
    auth?: string;
  };
};

export async function fetchReminderPublicKey(): Promise<{ publicKey: string; defaultTime: string }> {
  const response = await fetch('/api/reminders/public-key');
  if (!response.ok) {
    throw new Error(await reminderApiErrorMessage(response, 'Reminder public key unavailable'));
  }
  return response.json();
}

export async function saveReminderSubscription(args: {
  participantId: string;
  time: string;
  timezone: string;
  subscription: PushSubscriptionPayload;
}) {
  const response = await fetch('/api/reminders/subscriptions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  });
  if (!response.ok) {
    throw new Error(await reminderApiErrorMessage(response, 'Reminder subscription failed'));
  }
  return response.json();
}

export async function deleteReminderSubscription(endpoint: string) {
  const response = await fetch('/api/reminders/unsubscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ endpoint }),
  });
  if (!response.ok) {
    throw new Error(await reminderApiErrorMessage(response, 'Reminder unsubscribe failed'));
  }
  return response.json();
}

async function reminderApiErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string' && body.detail.length > 0) {
      return body.detail;
    }
  } catch {
    // Non-JSON failures still use the endpoint-specific fallback.
  }
  return fallback;
}
