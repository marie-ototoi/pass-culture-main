import React from 'react'
import { Provider } from 'react-redux'
import { BrowserRouter, Route, Switch } from 'react-router-dom'

import AppContainer from 'app/AppContainer'
import AppLayout from 'app/AppLayout'
import FirebaseContainer from 'components/firebase/FirebaseContainer'
import NotFound from 'components/pages/Errors/NotFound/NotFound'
import FeaturedRoute from 'components/router/FeaturedRoute'
import configureStore from 'store'
import routes, { routesWithMain } from 'utils/routes_map'

const { store } = configureStore()

const Root = () => {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <FirebaseContainer />
        <AppContainer>
          <Switch>
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
          </Switch>
        </AppContainer>
      </BrowserRouter>
    </Provider>
  )
}

export default Root
