import { RecommendedPhrasesDialog } from './RecommendedPhrasesDialog';

export function AdminHeader({ onRefresh }: { onRefresh: () => void }) {
  return (
    <header className="admin-header">
      <div>
        <span>Experiment dashboard</span>
        <h1>Validation Admin</h1>
      </div>
      <nav className="admin-actions" aria-label="Admin controls">
        <a href="/">Lesson app</a>
        <RecommendedPhrasesDialog />
        <button type="button" onClick={onRefresh}>
          Refresh
        </button>
      </nav>
    </header>
  );
}
