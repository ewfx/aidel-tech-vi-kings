// main.tsx - Application entry point with enhanced theme
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MantineProvider, createTheme, rem, ColorSchemeScript } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import App from './App';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './index.css';
import '@mantine/dates/styles.css'; 

// Define a custom theme for the application
const theme = createTheme({
  primaryColor: 'blue',
  colors: {
    blue: [
      '#e6f7ff',
      '#bae7ff',
      '#91d5ff',
      '#69c0ff',
      '#40a9ff',
      '#1890ff',
      '#096dd9',
      '#0050b3',
      '#003a8c',
      '#002766',
    ],
    // Add additional brand colors
    teal: [
      '#e6fcf5',
      '#c3fae8',
      '#96f2d7',
      '#63e6be',
      '#38d9a9',
      '#20c997',
      '#12b886',
      '#0ca678',
      '#099268',
      '#087f5b',
    ],
    indigo: [
      '#edf2ff',
      '#dbe4ff',
      '#bac8ff',
      '#91a7ff',
      '#748ffc',
      '#5c7cfa',
      '#4c6ef5',
      '#4263eb',
      '#3b5bdb',
      '#364fc7',
    ],
  },
  fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
  fontFamilyMonospace: 'Monaco, Courier, monospace',
  headings: { 
    fontFamily: 'Inter, system-ui, Avenir, Helvetica, Arial, sans-serif',
    fontWeight: '600',
  },
  defaultRadius: 'md',
  // Set default props for components to maintain consistent styling
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          transition: 'all 0.2s ease',
          fontWeight: 500,
        }
      }
    },
    Card: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          transition: 'box-shadow 0.2s ease, transform 0.2s ease',
        }
      }
    },
    Paper: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          transition: 'box-shadow 0.2s ease',
        }
      }
    },
    NavLink: {
      styles: {
        root: {
          transition: 'all 0.2s ease',
          fontWeight: 500,
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          }
        }
      }
    },
    AppShell: {
      styles: {
        main: {
          transition: 'padding-left 0.3s ease, padding-right 0.3s ease'
        }
      }
    },
    ThemeIcon: {
      styles: {
        root: {
          transition: 'all 0.2s ease',
        }
      }
    }
  },
  spacing: {
    xs: rem(4),
    sm: rem(8),
    md: rem(16),
    lg: rem(24),
    xl: rem(32),
  },
  breakpoints: {
    xs: '36em',
    sm: '48em',
    md: '62em',
    lg: '75em',
    xl: '88em',
  },
  // Enhance shadows
  shadows: {
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  // Set global styles
  other: {
    transitionTimings: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
    },
    borderRadiusRound: '30px',
  },
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <ColorSchemeScript defaultColorScheme="light" />
    <MantineProvider theme={theme} defaultColorScheme="light">
      <Notifications position="top-right" limit={5} />
      <App />
    </MantineProvider>
  </React.StrictMode>
);