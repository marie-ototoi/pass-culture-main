import { api } from 'apiClient/api'
import { GetUserHasBookingsAdapter } from 'core/Bookings'
import { GET_DATA_ERROR_MESSAGE } from 'core/shared'

const FAILING_RESPONSE: AdapterFailure<boolean> = {
  isOk: false,
  message: GET_DATA_ERROR_MESSAGE,
  payload: false,
}

export const getUserHasBookingsAdapter: GetUserHasBookingsAdapter =
  async () => {
    try {
      const { hasBookings } = await api.getUserHasBookings()

      return {
        isOk: true,
        message: null,
        payload: hasBookings,
      }
    } catch (e) {
      return FAILING_RESPONSE
    }
  }
