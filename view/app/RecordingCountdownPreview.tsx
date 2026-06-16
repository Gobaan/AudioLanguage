import { PromptedRecording, RecordingCountdownBar } from '../components';

export function RecordingCountdownPreview() {
  return (
    <section className="countdown-preview" aria-label="Recording countdown preview">
      <header className="countdown-preview-header">
        <span>Mic Timer Test</span>
        <h1>Recording countdown</h1>
      </header>
      <PromptedRecording
        prompt="Now you respond."
        startMode="manual"
        startLabel="Record"
        recordingMs={5000}
        reRecordLabel="Try again"
        modelReplayLabel=""
      />
      <div className="countdown-preview-reference" aria-label="Reference countdown states">
        <div className="prompted-recording recording">
          <p>Waiting for speech.</p>
          <RecordingCountdownBar durationMs={5000} />
        </div>
        <div className="prompted-recording recording">
          <p>Speaking detected.</p>
          <RecordingCountdownBar durationMs={5000} isPaused />
        </div>
      </div>
    </section>
  );
}
