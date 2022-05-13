import React from 'react'

import Spinner from 'components/layout/Spinner'
// TODO (rlecellier): rename into getOfferQueryParams
import { queryParamsFromOfferer } from 'components/pages/Offers/utils/queryParamsFromOfferer'
import {
  FORM_DEFAULT_VALUES,
  IOfferIndividualFormValues,
  setInitialFormValues,
} from 'new_components/OfferIndividualForm'
import { useGlobalErrorHandler } from 'routes/OfferIndividualCreation'
import { Informations as InformationsScreen } from 'screens/OfferIndividual/Informations'

import { createOfferAdapter } from './adapters'
import { useOffererNames, useOfferIndividualVenues } from './hooks'

const OfferIndividualCreationInformations = (): JSX.Element | null => {
  const globalErrorHandler = useGlobalErrorHandler()

  const { offererNames, isLoading: isOffererLoading } =
    useOffererNames(globalErrorHandler)
  const { offerIndividualVenues: venueList, isLoading: isVenueLoading } =
    useOfferIndividualVenues(globalErrorHandler)

  const { structure: offererId, lieu: venueId } =
    queryParamsFromOfferer(location)

  if (isOffererLoading || isVenueLoading) {
    return <Spinner />
  }

  const initialValues: IOfferIndividualFormValues = setInitialFormValues(
    FORM_DEFAULT_VALUES,
    offererNames,
    offererId,
    venueId,
    venueList
  )

  return (
    <InformationsScreen
      offererNames={offererNames}
      venueList={venueList}
      createOfferAdapter={createOfferAdapter}
      initialValues={initialValues}
    />
  )
}

export default OfferIndividualCreationInformations
