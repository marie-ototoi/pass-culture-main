import { apiV1 } from 'api/api'
import { SharedCurrentUserResponseModel } from 'api/v1/gen'

import { IUser } from '../types'

type TPostOfferAdapter = Adapter<null, IUser, null>

const NO_USER_RESPONSE: AdapterFailure<null> = {
  isOk: false,
  message: "L'utilisateur n'est pas loggé",
  payload: null,
}

const serializeUser = (apiUser: SharedCurrentUserResponseModel): IUser => {
  return {
    id: apiUser.id,
    civility: apiUser.civility || null,
    firstName: apiUser.firstName || null,
    lastName: apiUser.lastName || null,
    isAdmin: apiUser.isAdmin,
    email: apiUser.email,
    address: apiUser.address || null,
    postalCode: apiUser.postalCode || null,
    city: apiUser.city || null,
    phoneNumber: apiUser.phoneNumber || null,
    hasSeenProTutorials: apiUser.hasSeenProTutorials || false,
  }
}

const getUserAdapter: TPostOfferAdapter = async () => {
  try {
    const response = await apiV1.getUsersGetProfile()
    return {
      isOk: true,
      message: 'success',
      payload: serializeUser(response),
    }
  } catch {
    return NO_USER_RESPONSE
  }
}

export default getUserAdapter
