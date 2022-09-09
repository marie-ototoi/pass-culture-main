import React from 'react'
import { BrowserRouter } from 'react-router-dom'

import { App, AppRouter } from 'app'
import NavigationLogger from 'components/router/NavigationLogger'
import { AnalyticsContextProvider } from 'context/analyticsContext'
import StoreProvider from 'store/StoreProvider/StoreProvider'

const Root = (): JSX.Element => {
  return (
    <StoreProvider>
      <AnalyticsContextProvider>
        <BrowserRouter>
          <NavigationLogger />
          <App>
            <AppRouter />
          </App>
        </BrowserRouter>
      </AnalyticsContextProvider>
    </StoreProvider>
  )
}

export default Root
