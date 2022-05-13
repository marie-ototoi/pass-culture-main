import {DataProvider, GetListParams} from 'react-admin'
import {UserSearchInterface, UserApiInterface} from "../resources/Interfaces/UserSearchInterface";
import {stringify} from "querystring";

let assets: UserApiInterface[] = []

export const dataProvider: DataProvider = {
    // @ts-ignore see later
    async searchList(resource: string, params: string) {
        switch (resource) {
            default:
            case 'public_users/search':
                // const response = await fetch(`https://backend.testing.passculture.team/backoffice/${resource}?q=`+ params)
                const response = await fetch(`http://localhost/backoffice/${resource}?q=`+ params)
                const json: UserSearchInterface = await response.json()
                assets = json.accounts
                    .map((item) => ({
                        ...item,
                        id: item.id,
                    }))

                assets = assets
                    .filter((obj, pos, arr) => arr.map(({id}) => id).indexOf(obj.id) === pos)

                return {
                    data: assets,
                    total: assets.length,
                }

        }
    },
    // @ts-ignore see later
    async getList(resource, params) {

        if (resource.includes('/')) {
            switch (resource) {
                default:
                case 'public_users/search':
                    if (assets.length === 0) {
                        // @ts-ignore
                        const response = await fetch(`https://backend.testing.passculture.team/backoffice/public_accounts/search/?q=${params}`)
                        const json: UserSearchInterface = await response.json()
                        assets = json.accounts
                            .map((item) => ({
                                ...item,
                                id: item.id,
                            }))

                        assets = assets
                            .filter((obj, pos, arr) => arr.map(({id}) => id).indexOf(obj.id) === pos)
                    }

                    return {
                        data: assets,
                        total: assets.length,
                    }
            }
        }
        return {
            data: [],
            total: 0,
        }
    },
    // @ts-ignore
    async getOne(resource, params) {
        return {
            data: {
                id: 0,
            },
        }
    },
    async getMany(resource, params) {
        return {
            data: [],
            total: 0,
        }
    },
    async getManyReference(resource, params) {
        return {
            data: [],
            total: 0,
        }
    },
    // @ts-ignore
    async create(resource, params) {
        return {
            data: {
                id: 0,
            },
        }
    },
    // @ts-ignore
    async update(resource, params) {
        return {
            data: {
                id: 1,
            },
        }
    },
    async updateMany(resource, params) {
        return {
            data: [],
        }
    },
    // @ts-ignore
    async delete(resource, params) {
        return {
            data: {
                id: 1,
            },
        }
    },
    async deleteMany(resource, params) {
        return {
            data: [],
        }
    },
}
