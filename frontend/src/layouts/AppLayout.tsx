import { makeStyles } from '@fluentui/react-components';
import { Outlet } from 'react-router-dom';
import { tokensX } from '../theme';
import { Sidebar } from './Sidebar';

const useStyles = makeStyles({
  shell: {
    display: 'flex',
    minHeight: '100vh',
  },
  main: {
    flex: 1,
    minWidth: 0,
    backgroundColor: tokensX.canvas,
  },
});

export function AppLayout() {
  const styles = useStyles();
  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <div className="content-area">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
