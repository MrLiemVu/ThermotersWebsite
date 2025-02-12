import HistoryTable from '../components/HistoryTable';
import { useAuth } from '../contexts/AuthContext';

const HistoryPage = () => {
  const { currentUser } = useAuth();
  
  return (
    <div>
      <h1>Job History</h1>
      {currentUser ? (
        <HistoryTable currentUser={currentUser} />
      ) : (
        <p>Please log in to view your job history</p>
      )}
    </div>
  );
};

export default HistoryPage; 