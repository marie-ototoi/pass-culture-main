import { getUserAdapter } from 'core/Users/adapters'
import * as pcapi from 'repository/pcapi/pcapi'
import { setUsers } from 'store/reducers/data'

import { setIsInitialized } from './actions'

export const loadUser = () => dispatch => {
  const response = await getUserAdapter()
  let user = null
  if (response.isOk) {
    user = response.payload
  }

  dispatch(setUsers([user]))
  dispatch(setIsInitialized(true))
}

export const signin = (emailValue, passwordValue, success, fail) => dispatch =>
  pcapi
    .signin({
      identifier: emailValue,
      password: passwordValue,
    })
    .then(user => {
      // TODO: state.data.users have to be moved into state.user.currentUser
      dispatch(setUsers([user ? user : null]))
      success()
    })
    .catch(payload => {
      setUsers([null])
      fail(payload)
    })
