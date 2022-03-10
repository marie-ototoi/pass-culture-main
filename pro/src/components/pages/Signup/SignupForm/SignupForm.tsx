import createDecorator from 'final-form-calculate'
import React from 'react'
import { Field, Form } from 'react-final-form'
import { Link } from 'react-router-dom'

import FieldErrors from 'components/layout/form/FieldErrors'
import PasswordField from 'components/layout/form/fields/PasswordField'
import Icon from 'components/layout/Icon'
import { LegalInfos } from 'components/layout/LegalInfos/LegalInfos'
import bindAddressAndDesignationFromSiren from 'repository/siren/bindSirenFieldToDesignation'

import SirenField from './SirenField/SirenField'

const required = (value: string) => (value ? undefined : 'Required')

const addressAndDesignationFromSirenDecorator = createDecorator({
  field: 'siren',
  updates: bindAddressAndDesignationFromSiren,
})

interface ISignupForm {
  createNewProUser: () => void
  currentUser: {} | null
  errors: {}
  history: () => void
  location: {}
  notifyError: (message: string) => void
  redirectToConfirmation: () => void
}

const SignupForm = ({
  createNewProUser,
  currentUser,
  errors,
  history,
  location,
  notifyError,
  redirectToConfirmation,
}: ISignupForm): JSX.Element => {

  const onHandleSuccess = () => {
    redirectToConfirmation()
  }

  const onHandleFail = () => {
    notifyError('Une ou plusieurs erreurs sont présentes dans le formulaire.')
  }

  const handleSubmit = values => {
    createNewProUser(values, onHandleFail, onHandleSuccess)
  }

  return (
    <section className="sign-up-form-page">
      <div className="content">
        <h1>Créer votre compte professionnel</h1>
        <h2>Merci de compléter les champs suivants pour créer votre compte.</h2>
        <div className="sign-up-operating-procedures">
          <div>
            Nous vous invitons à prendre connaissance des modalités de
            fonctionnement avant de renseigner les champs suivants.
          </div>
          <a
            className="tertiary-link"
            href="https://docs.passculture.app/le-pass-culture-en-quelques-mots"
            rel="noopener noreferrer"
            target="_blank"
          >
            <Icon svg="ico-external-site" />
            <span>Fonctionnement du pass Culture pro</span>
          </a>
          <a
            className="tertiary-link"
            href="https://passculture.zendesk.com/hc/fr/articles/4411999179665"
            rel="noopener noreferrer"
            target="_blank"
          >
            <Icon svg="ico-external-site" />
            <span>Consulter notre centre d’aide</span>
          </a>
        </div>
        <div className="sign-up-tips">
          Tous les champs sont obligatoires sauf mention contraire
        </div>
        <div>{}</div>
        <Form
          decorators={[addressAndDesignationFromSirenDecorator]}
          onSubmit={this.handleSubmit}
        >
          {({ handleSubmit, valid, values }) => (
            <form onSubmit={handleSubmit}>
              <Field
                component={this.renderEmailTextField}
                name="email"
                type="text"
                validate={required}
              />

              <PasswordField
                errors={errors ? errors.password : null}
                label="Mot de passe"
                name="password"
                showTooltip
              />

              <Field
                component={this.renderNameTextField}
                name="lastName"
                required
                validate={required}
              />

              <Field
                component={this.renderFirstNameTextField}
                name="firstName"
                validate={required}
              />

              <Field
                component={this.renderPhoneNumberField}
                name="phoneNumber"
                required
                validate={required}
              />

              <SirenField value={values.name} />

              <label className="sign-up-checkbox" htmlFor="sign-up-checkbox">
                <Field
                  component="input"
                  id="sign-up-checkbox"
                  name="contactOk"
                  type="checkbox"
                />
                <span>
                  J’accepte d’être contacté par e-mail pour recevoir les
                  nouveautés du pass Culture et contribuer à son amélioration
                  (facultatif)
                </span>
                <FieldErrors customMessage={errors ? errors.contactOk : null} />
              </label>
              <LegalInfos
                className="sign-up-infos-before-signup"
                title="Créer mon compte"
              />
              <div className="buttons-field">
                <Link className="secondary-link" to="/connexion">
                  J’ai déjà un compte
                </Link>
                <button
                  className="primary-button"
                  disabled={!valid}
                  type="submit"
                >
                  Créer mon compte
                </button>
              </div>
            </form>
          )}
        </Form>
      </div>
    </section>
  )
}

export default SignupForm
