import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { IUser } from 'core/Users/types'
import { selectCurrentUser } from 'store/selectors/data/usersSelectors'
import { selectUserInitialized } from 'store/user/selectors'
import { loadUser } from 'store/user/thunks'
export interface IUseCurrentUserReturn {
  isUserInitialized: boolean
  currentUser: IUser | null
}

const useCurrentUser = (): IUseCurrentUserReturn => {
  const currentUser = useSelector(state => selectCurrentUser(state))
  const isUserInitialized = useSelector(state => selectUserInitialized(state))

  const dispatch = useDispatch()
  useEffect(() => {
    if (!isUserInitialized) {
      dispatch(loadUser())
    }
  }, [dispatch, isUserInitialized])

  return { isUserInitialized, currentUser }
}

export default useCurrentUser
