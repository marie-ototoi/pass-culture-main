import { Form, FormikProvider, useFormik } from 'formik'
import React, { useEffect } from 'react'
import { useHistory, useLocation } from 'react-router-dom'

import useCurrentUser from 'components/hooks/useCurrentUser'
import useNotification from 'components/hooks/useNotification'
import LegalInfos from 'components/layout/LegalInfos/LegalInfos'
import { redirectLoggedUser } from 'components/router/helpers'
import { BannerRGS } from 'new_components/Banner'
import * as pcapi from 'repository/pcapi/pcapi'
import { Button, SubmitButton, TextInput } from 'ui-kit'
import { Checkbox } from 'ui-kit'
import { ButtonVariant } from 'ui-kit/Button/types'
import { removeWhitespaces } from 'utils/string'

import OperatingProcedures from './OperationProcedures'
import SirenInput from 'ui-kit/form/SirenInput'
import { getSirenDataAdapter } from 'core/Offerers/adapters'
import PasswordInput from 'ui-kit/form/PasswordInput'
import { validationSchema } from './validationSchema'
import { ISignupApiErrorResponse, ISignupFormValues } from './types'
import { SIGNUP_FORM_DEFAULT_VALUES } from './constants'


const SignupForm = (): JSX.Element => {
  const history = useHistory()
  const notification = useNotification()
  const { currentUser } = useCurrentUser()
  const location = useLocation()

  useEffect(() => {
    console.log("useEffectRedirection")
    redirectLoggedUser(history, location, currentUser)
  }, [currentUser])

  useEffect(() => {
    const script = document.createElement('script')

    script.src = '//js.hs-scripts.com/5119289.js'
    script.async = true
    script.type = 'text/javascript'
    script.id = 'hs-script-loader'
    script.defer = true

    document.body.appendChild(script)
    return () => {
      const script = document.getElementById('hs-script-loader') as Node
      document.body.removeChild(script)
    }
  }, [])

  const onSubmit = (values: ISignupFormValues) => {
    const { legalUnitValues, ...flattenvalues } = values
    const { firstName, siren } = flattenvalues
    pcapi
      .signup({
        ...flattenvalues,
        ...legalUnitValues,
        siren: removeWhitespaces(siren),
        publicName: firstName,
      })
      .then(() => onHandleSuccess())
      .catch(response => onHandleFail(response.errors ? response.errors : {}))
  }

  const onHandleSuccess = () => {
    history.replace('/inscription/confirmation')
  }

  const onHandleFail = (errors: ISignupApiErrorResponse) => {
    for (let field in errors)
      formik.setFieldError(field, (errors as any)[field])

    notification.error(
      'Une ou plusieurs erreurs sont présentes dans le formulaire.'
    )
  }

  const formik = useFormik({
    initialValues: SIGNUP_FORM_DEFAULT_VALUES,
    onSubmit: onSubmit,
    validationSchema,
    validateOnChange: false,
  })

  const getSirenAPIData = async (siren: string) => {
    const response = await getSirenDataAdapter(siren)
    if (response.isOk)
      formik.setFieldValue('legalUnitValues', response.payload.values)
    else formik.setFieldError('siren', response.message)
  }

  return (
    <section className="sign-up-form-page">
      <div className="content">
        <h1>Créer votre compte professionnel</h1>
        <h2>Merci de compléter les champs suivants pour créer votre compte.</h2>
        <OperatingProcedures />

        <div className="sign-up-tips">
          Tous les champs sont obligatoires sauf mention contraire
        </div>
        <FormikProvider value={formik}>
          <Form onSubmit={formik.handleSubmit}>
            <div className="sign-up-form">
              <TextInput
                label="Adresse e-mail"
                name="email"
                placeholder="nom@example.fr"
              />
              <PasswordInput
                name="password"
                label="Mot de passe"
                placeholder="Mon mot de passe"
              />
              <TextInput label="Nom" name="lastName" placeholder="Mon nom" />
              <TextInput
                label="Prénom"
                name="firstName"
                placeholder="Mon prénom"
              />
              <TextInput
                label="Téléphone (utilisé uniquement par l’équipe du pass Culture)"
                name="phoneNumber"
                placeholder="Mon numéro de téléphone"
              />
              <div className="siren-field">
                <SirenInput
                  label="SIREN de la structure que vous représentez"
                  onValidSiren={getSirenAPIData}
                />
                <span className="field-siren-value">
                  {formik.values.legalUnitValues.name}
                </span>
              </div>
              <Checkbox
                hideFooter
                label="J’accepte d’être contacté par e-mail pour recevoir les
                      nouveautés du pass Culture et contribuer à son
                      amélioration (facultatif)"
                name="contactOk"
                value={formik.values.contactOk}
              />
              <LegalInfos
                className="sign-up-infos-before-signup"
                title="Créer mon compte"
              />
              <BannerRGS />
            </div>
            <div className="buttons-field">
              <Button
                onClick={() => history.push('/connexion')}
                variant={ButtonVariant.SECONDARY}
              >
                J’ai déjà un compte
              </Button>
              <SubmitButton className="primary-button" isLoading={formik.isSubmitting} disabled={!formik.dirty || !formik.isValid}>
                Créer mon compte
              </SubmitButton>
            </div>
          </Form>
        </FormikProvider>
      </div>
    </section>
  )
}

export default SignupForm
