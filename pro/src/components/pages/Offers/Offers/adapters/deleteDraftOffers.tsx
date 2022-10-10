import { api } from 'apiClient/api'

import { computeDeletionSuccessMessage } from './utils'

type UpdateAllCollectiveOffersActiveStatusAdapter = Adapter<
  {
    ids: string[]
    nbSelectedOffers?: number
  },
  null,
  null
>

export const deleteDraftOffersAdapter: UpdateAllCollectiveOffersActiveStatusAdapter =
  async ({ ids, nbSelectedOffers = 1 }) => {
    try {
      await api.deleteDraftOffers({
        ids,
      })

      return {
        isOk: true,
        message: computeDeletionSuccessMessage(nbSelectedOffers),
        payload: null,
      }
    } catch (error) {
      return {
        isOk: false,
        payload: null,
        message: `Une erreur est survenue lors de la suppression du brouillon`,
      }
    }
  }
