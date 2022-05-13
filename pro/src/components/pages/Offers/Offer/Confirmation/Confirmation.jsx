import { Link, useLocation } from 'react-router-dom'
import React, { useCallback } from 'react'

import { DisplayOfferInAppLink } from 'components/pages/Offers/Offer/DisplayOfferInAppLink'
import { OFFER_STATUS_PENDING } from 'core/Offers/constants'
import { ReactComponent as PendingIcon } from 'components/pages/Offers/Offer/Confirmation/assets/pending.svg'
import PropTypes from 'prop-types'
import { Redirect } from 'react-router'
import { ReactComponent as ValidateIcon } from 'components/pages/Offers/Offer/Confirmation/assets/validate.svg'
import { queryParamsFromOfferer } from 'components/pages/Offers/utils/queryParamsFromOfferer'
import { useOfferEditionURL } from 'components/hooks/useOfferEditionURL'

const Confirmation = ({ isCreatingOffer, offer, setOffer }) => {
  const editionUrl = useOfferEditionURL(offer.isEducational, offer.id)
  const location = useLocation()

  const resetOffer = useCallback(() => {
    setOffer(null)
  }, [setOffer])

  const isPendingOffer = offer.status === OFFER_STATUS_PENDING
  if (!isCreatingOffer && !isPendingOffer) {
    return <Redirect to={editionUrl} />
  }

  let queryString = ''
  const queryParams = queryParamsFromOfferer(location)
  if (queryParams.structure !== '') {
    queryString = `?structure=${queryParams.structure}`
  }

  if (queryParams.lieu !== '') {
    queryString += `&lieu=${queryParams.lieu}`
  }

  return (
    <div className="offer-confirmation">
      {isPendingOffer ? (
        <div>
          <PendingIcon className="oc-pending" />
          <h2 className="oc-title">Offre en cours de validation</h2>
          <p className="oc-details">
            Votre offre est en cours de validation par l’équipe pass Culture,
            nous vérifions actuellement son éligibilité.
            <b> Cette vérification pourra prendre jusqu’à 72h.</b> Vous recevrez
            un email de confirmation une fois votre offre validée et disponible
            à la réservation.
          </p>
        </div>
      ) : (
        <div>
          <ValidateIcon className="oc-validate" />
          <h2 className="oc-title">Offre créée !</h2>
          <p className="oc-details">
            Votre offre est désormais disponible à la réservation sur
            l’application pass Culture.
          </p>
        </div>
      )}
      <div className="oc-actions">
        <DisplayOfferInAppLink nonHumanizedId={offer.nonHumanizedId} />
        <Link
          className="primary-link"
          onClick={resetOffer}
          to={`/offre/creation/individuel${queryString}`}
        >
          Créer une nouvelle offre
        </Link>
      </div>
    </div>
  )
}

Confirmation.propTypes = {
  isCreatingOffer: PropTypes.bool.isRequired,
  offer: PropTypes.shape().isRequired,
  setOffer: PropTypes.func.isRequired,
}

export default Confirmation
