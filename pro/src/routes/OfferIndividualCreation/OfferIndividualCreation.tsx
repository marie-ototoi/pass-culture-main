import React from 'react'

import Breadcrumb, { BreadcrumbStyle } from 'new_components/Breadcrumb'
import { OfferFormLayout } from 'new_components/OfferFormLayout'
import { OFFER_FORM_STEP_IDS, useOfferFormSteps } from 'core/Offers'
import { fakeOffer } from 'screens/OfferIndividual/constants'
import { OfferIndividualCreationInformations as InformationsRoute } from 'routes/OfferIndividualCreationInformations'
import { OfferIndividualCreationStocks as StockRoute } from 'routes/OfferIndividualCreationStocks'
import { OfferIndividualCreationSummary as ConfirmationRoute } from 'routes/OfferIndividualCreationSummary'

const OfferIndividualCreation = (): JSX.Element => {
  const { currentStep, stepList } = useOfferFormSteps(fakeOffer)

  return (
    <OfferFormLayout>
      <OfferFormLayout.TitleBlock>
        <h1>Créer une offe</h1>
      </OfferFormLayout.TitleBlock>

      <OfferFormLayout.Stepper>
        <Breadcrumb
          activeStep={currentStep.id}
          steps={stepList}
          styleType={BreadcrumbStyle.TAB}
        />
      </OfferFormLayout.Stepper>

      <OfferFormLayout.Content>
        {currentStep.id === OFFER_FORM_STEP_IDS.INFORMATIONS && (
          <InformationsRoute />
        )}
        {currentStep.id === OFFER_FORM_STEP_IDS.STOCKS && <StockRoute />}
        {currentStep.id === OFFER_FORM_STEP_IDS.SUMMARY && (
          <ConfirmationRoute />
        )}
      </OfferFormLayout.Content>
    </OfferFormLayout>
  )
}

export default OfferIndividualCreation
