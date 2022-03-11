import React from 'react'
import { Route, Routes, useMatch } from 'react-router-dom'

import NotFound from 'components/pages/Errors/NotFound/NotFound'

import VenueCreationContainer from './VenueCreation/VenueCreationContainer'
import VenueEditionContainer from './VenueEdition/VenueEditionContainer'

const VenueLayout = () => {
  const match = useMatch()
  return (
    <Routes>
      <Route exact path={`${match.path}/creation`}>
        <VenueCreationContainer />
      </Route>
      <Route exact path={`${match.path}/:venueId([A-Z0-9]+)`}>
        <VenueEditionContainer />
      </Route>
      <Route>
        <NotFound />
      </Route>
    </Routes>
  )
}

export default VenueLayout
