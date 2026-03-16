import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
      <h1
        className="text-6xl font-extrabold tracking-tight"
        style={{ color: '#f59e0b' }}
      >
        404
      </h1>
      <p className="mt-4 text-lg text-zinc-400">
        This sector doesn't exist.
      </p>
      <Link
        to="/dashboard"
        className="mt-8 px-6 py-2 rounded-lg font-semibold text-black transition-colors"
        style={{ backgroundColor: '#f59e0b' }}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#d97706')}
        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#f59e0b')}
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
