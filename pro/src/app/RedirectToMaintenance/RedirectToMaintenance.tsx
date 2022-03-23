import { URL_FOR_MAINTENANCE } from 'utils/config'

const RedirectToMaintenance = () => {
  window.location.href = URL_FOR_MAINTENANCE || ''
  return null
}

export default RedirectToMaintenance
