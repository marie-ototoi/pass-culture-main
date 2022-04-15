import React from 'react';
import { Admin, Resource } from 'react-admin'
import CssBaseline from '@mui/material/CssBaseline'
import { dataProvider } from './providers/dataProvider'
import { SignalList } from './resources/Signals/SignalList'
import { SignalCreate } from './resources/Signals/SignalCreate'
import { authProvider } from './providers/authProvider'
import { createBrowserHistory } from 'history'
import { i18nProvider } from './providers/i18nProvider'

const history = createBrowserHistory()

function App() {
  return (
    <>
      <CssBaseline />
      <Admin
        history={history}
        dataProvider={dataProvider}
        authProvider={authProvider}
        i18nProvider={i18nProvider}
      >
        {/* the bullishers */}
        <Resource name="thebullishers/api/v1/signals" list={SignalList} create={SignalCreate} />

        {/* binance */}
        <Resource name="binance/api/v1/exchangeInfo" />
      </Admin>
    </>
  )
}

export default App
