import React from 'react'
import { Provider } from 'react-redux'
import { Router, Route, Routes, Navigate } from 'react-router'

import AppContainer from 'app/AppContainer'
import AppLayout from 'app/AppLayout'
import NotFound from 'components/pages/Errors/NotFound/NotFound'
import FeaturedRoute from 'components/router/FeaturedRoute'
import NavigationLogger from 'components/router/NavigationLogger'
import configureStore from 'store'
import routes, { routesWithMain } from 'utils/routes_map'

const { store } = configureStore()

const Root = () => {
  return (
    <Provider store={store}>
      <Router>
        <NavigationLogger />
        <AppContainer>
          <Routes>
            <Navigate
              from="/offres/:offerId([A-Z0-9]+)/edition"
              to="/offre/:offerId([A-Z0-9]+)/individuel/edition"
            />
            <Navigate
              from="/offre/:offerId([A-Z0-9]+)/scolaire/edition"
              to="/offre/:offerId([A-Z0-9]+)/collectif/edition"
            />
            {routes.map(route => {
              return (
                <FeaturedRoute
                  exact={route.exact}
                  featureName={route.featureName}
                  key={route.path}
                  path={route.path}
                >
                  <AppLayout
                    layoutConfig={route.meta && route.meta.layoutConfig}
                  >
                    <route.component />
                  </AppLayout>
                </FeaturedRoute>
              )
            })}

            {routesWithMain.map(route => {
              // first props, last overrides
              return (
                <FeaturedRoute
                  {...route}
                  exact={route.exact}
                  key={route.path}
                />
              )
            })}
            <Route component={NotFound} />
          </Routes>
        </AppContainer>
      </Router>
    </Provider>
  )
}

export default Root
