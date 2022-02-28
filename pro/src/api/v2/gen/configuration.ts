// tslint:disable
/**
 * pass Culture pro public API v2
 * No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)
 *
 * OpenAPI spec version: 2
 * 
 *
 * NOTE: This file is auto generated by the swagger code generator program.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the file manually.
 */
export interface APIConfigurationParameters {
  apiKey?: string | ((name: string) => string);
  username?: string;
  password?: string;
  accessToken?: string | ((name: string, scopes?: string[]) => string);
  basePath?: string;
}

export class APIConfiguration {
  /**
   * parameter for apiKey security
   * @param name security name
   * @memberof APIConfiguration
   */
  apiKey?: string | ((name: string) => string);
  /**
   * parameter for basic security
   *
   * @type {string}
   * @memberof APIConfiguration
   */
  username?: string;
  /**
   * parameter for basic security
   *
   * @type {string}
   * @memberof APIConfiguration
   */
  password?: string;
  /**
   * parameter for oauth2 security
   * @param name security name
   * @param scopes oauth2 scope
   * @memberof APIConfiguration
   */
  accessToken?: string | ((name: string, scopes?: string[]) => string);
  /**
   * override base path
   *
   * @type {string}
   * @memberof APIConfiguration
   */
  basePath?: string;

  constructor(param: APIConfigurationParameters = {}) {
    this.apiKey = param.apiKey;
    this.username = param.username;
    this.password = param.password;
    this.accessToken = param.accessToken;
    this.basePath = param.basePath;
  }
}