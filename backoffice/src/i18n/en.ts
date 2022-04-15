import { all } from 'deepmerge'
import ra from 'ra-language-english'
import { TranslationMessages } from 'react-admin'

const messages = all([ra]) as TranslationMessages

export default messages
