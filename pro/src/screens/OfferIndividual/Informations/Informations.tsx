import { useFormik, FormikProvider } from 'formik'
import React from 'react'
import { useHistory } from 'react-router-dom'

import Spinner from 'components/layout/Spinner'
import { TOffererName } from 'core/Offerers/types'
import { TOfferIndividualVenue } from 'core/Venue/types'
import { OfferFormLayout } from 'new_components/OfferFormLayout'
import {
  OfferIndividualForm,
  IOfferIndividualFormValues,
  validationSchema,
} from 'new_components/OfferIndividualForm'
import { OFFER_FORM_STEP_IDS } from 'screens/OfferIndividual/constants'

import { ActionBar } from '../ActionBar'
import { fakeOffer } from '../constants'
import { getStepsOffer } from '../utils/steps'

export interface IInformationsProps {
  createOfferAdapter: (
    formValues: IOfferIndividualFormValues
  ) => Promise<string | void>
  initialValues: IOfferIndividualFormValues
  isParentReady: boolean
  offererNames: TOffererName[]
  venueList: TOfferIndividualVenue[]
}

const Informations = ({
  createOfferAdapter,
  initialValues,
  isParentReady,
  offererNames,
  venueList,
}: IInformationsProps): JSX.Element => {
  const history = useHistory()

  // call getStep with offer when this screen get it as prop
  const { activeSteps } = getStepsOffer(fakeOffer)
  const handleNextStep = async () => formik.handleSubmit()

  const onSubmit = async (formValues: IOfferIndividualFormValues) => {
    await createOfferAdapter(formValues)
    // TODO get a real id after offer creation form submit
    history.push(`/offre/${fakeOffer.id}/v3/creation/individuelle/stocks`)
  }

  const { resetForm, ...formik } = useFormik({
    initialValues,
    onSubmit,
    validationSchema,
  })

  return (
    <FormikProvider value={{ ...formik, resetForm }}>
      <form onSubmit={formik.handleSubmit}>
        {isParentReady ? (
          <OfferIndividualForm
            offererNames={offererNames}
            venueList={venueList}
          />
        ) : (
          <Spinner />
        )}

        <OfferFormLayout.ActionBar>
          <ActionBar
            disableNext={!activeSteps.includes(OFFER_FORM_STEP_IDS.STOCKS)}
            onClickNext={handleNextStep}
          />
        </OfferFormLayout.ActionBar>
      </form>
    </FormikProvider>
  )
}

export default Informations
