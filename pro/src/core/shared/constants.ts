export const urlRegex = new RegExp(
  // eslint-disable-next-line no-useless-escape
  /^(?:http(s)?:\/\/)?[\w.-\.-\.@]+(?:\.[\w\.-\.@]+)+[\w\-\._~:\/?#[\]@%!\$&'\(\)\*\+,;=.]+$/,
  'i'
)

export const offerFormUrlRegex = new RegExp(
  /*eslint-disable-next-line no-useless-escape*/
  /^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)(([a-z0-9]+([\-\.\.-\.@_a-z0-9]+)*\.[a-z]{2,5})|((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d))(:[0-9]{1,5})?\S*?$/,
  'i'
)

export const PATCH_SUCCESS_MESSAGE =
  'Vos modifications ont bien été enregistrées'
export const GET_DATA_ERROR_MESSAGE =
  'Nous avons rencontré un problème lors de la récupération des données.'
export const SENT_DATA_ERROR_MESSAGE =
  'Une erreur est survenue lors de la sauvegarde de vos modifications.\n Merci de réessayer plus tard'
export const FORM_ERROR_MESSAGE =
  'Une ou plusieurs erreurs sont présentes dans le formulaire'

export const NBSP = '\u00a0'
