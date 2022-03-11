import PropTypes from 'prop-types'
import React from 'react'
import { Navigate, Route, Routes, useParams, useMatch } from 'react-router-dom'

import PageTitle from 'components/layout/PageTitle/PageTitle'
import Titles from 'components/layout/Titles/Titles'

import Breadcrumb, { mapPathToStep, STEP_ID_INFORMATIONS } from '../Breadcrumb'

const VenueCreation = ({ isTemporary }) => {
  let { offererId, venueId } = useParams()

  const match = useMatch()
  const pageTitle = isTemporary ? 'Créer un lieu temporaire' : 'Créer un lieu'

  const stepName = location.pathname.match(/[a-z]+$/)
  const activeStep = stepName
    ? mapPathToStep[stepName[0]]
    : STEP_ID_INFORMATIONS

  return (
    <div>
      <PageTitle title={pageTitle} />
      <Titles title={pageTitle} />

      <Breadcrumb
        activeStep={activeStep}
        offererId={offererId}
        venueId={venueId}
      />

      <Routes>
        <Route exact path={`${match.path}/informations`}>
          <p>
            {isTemporary
              ? 'create temporary venue information form'
              : 'create venue information form'}
          </p>
        </Route>
        <Route exact path={`${match.path}/gestion`}>
          <p>create venue management form</p>
        </Route>
        <Route exact path={match.path}>
          <Navigate to={`${match.url}/informations`} />
        </Route>
      </Routes>
    </div>
  )
}

VenueCreation.defaultProps = {
  isTemporary: false,
}

VenueCreation.propTypes = {
  isTemporary: PropTypes.bool,
}

export default VenueCreation
