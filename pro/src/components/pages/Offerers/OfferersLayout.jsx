import React from 'react'
import { Route, Routes, useMatch } from 'react-router'

import NotFound from 'components/pages/Errors/NotFound/NotFound'

import OfferersContainer from './List/OfferersContainer'
import OffererDetailsLayout from './Offerer/OffererDetailsLayout'
import OffererCreationContainer from './OffererCreation/OffererCreationContainer'

const OfferersLayout = () => {
  const match = useMatch()

  return (
    <Routes>
      <Route exact path={match.path}>
        <OfferersContainer />
      </Route>
      <Route exact path={`${match.path}/creation`}>
        <OffererCreationContainer />
      </Route>
      <Route path={`${match.path}/:offererId([A-Z0-9]+)`}>
        <OffererDetailsLayout />
      </Route>
      <Route>
        <NotFound />
      </Route>
    </Routes>
  )
}

export default OfferersLayout
