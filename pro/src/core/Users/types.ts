import { GenderEnum } from 'api/v1/gen'

export interface IUser {
  address: string | null
  city: string | null
  civility: GenderEnum | null
  email: string
  firstName: string | null
  hasSeenProTutorials: boolean
  id: string
  isAdmin: boolean
  lastName: string | null
  phoneNumber: string | null
  postalCode: string | null
}
