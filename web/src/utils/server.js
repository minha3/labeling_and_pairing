import API from "./API";

class Server extends API {
    constructor(errorHandler) {
        super(errorHandler);
        this.apibase = 'http://localhost:8000';
    }

    join_param(query) {
        if (query === undefined) {
            return '';
        }
        let str = '';
        for (const [key, value] of Object.entries(query)) {
            if (value === undefined || value === '') {
                // pass
            }
            else if (value.constructor === Array) {
                for (let i = 0; i < value.length; i++) {
                    str += `&${key}=${encodeURIComponent(value[i])}`;
                }
            }
            else if (value.constructor === String && value.includes(',')) {
                let token = value.split(',')
                for (let i = 0; i < token.length; i++) {
                    str += `&${key}=${encodeURIComponent(token[i])}`;
                }
            }
            else if (value.constructor === Object) {
                for (const [_key, _value] of Object.entries(value)) {
                    if (_value.constructor === Array) {
                        for (let i=0; i<_value.length; i++) {
                            str += `&${key}=${encodeURIComponent(_key)}=${encodeURIComponent(_value[i])}`
                        }
                    }
                    else {
                        str += `&${key}=${encodeURIComponent(_key)}=${encodeURIComponent(_value)}`
                    }
                }
            }
            else {
                str += `&${key}=${encodeURIComponent(value)}`;
            }
        }
        return str
    }

    ping() {
        return this.GET(`${this.apibase}/ping`)
    }

    create_file(data) {
        const formData = new FormData();
        formData.append("file", data);
        return this.POST(`${this.apibase}/files`, formData)
    }

    get_files() {
        return this.GET(`${this.apibase}/files`)
    }

    get_file(fileId) {
        return this.GET(`${this.apibase}/files/${fileId}`)
    }

    delete_file(fileId) {
        return this.DELETE(`${this.apibase}/files/${fileId}`)
    }
}

export default Server