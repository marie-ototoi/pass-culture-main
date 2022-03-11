import React from 'react'
import { Route, Routes, useMatch } from 'react-router-dom'

import NotFound from 'components/pages/Errors/NotFound/NotFound'

import VenueCreation from './VenueCreation/VenueCreation'
import VenueEdition from './VenueEdition/VenueEdition'

const VenueLayout = () => {
  const match = useMatch()

  return (
    <Routes>
      <Route path={`${match.path}/creation`}>
        <VenueCreation />
      </Route>
      <Route path={`${match.path}/temporaire/creation`}>
        <VenueCreation isTemporary />
      </Route>
      <Route path={`${match.path}/:venueId([A-Z0-9]+)`}>
        <VenueEdition />
      </Route>
      <Route>
        <NotFound />
      </Route>
    </Routes>
  )
}

export default VenueLayout
