class API {
    constructor(errorHandler) {
        this.errorHandler = errorHandler;
    }

    isDict(data) {
        return typeof data === "object" && !Array.isArray(data);
    }

    isArray(data) {
        return typeof data === "object" && Array.isArray(data);
    }

    GET(url) {
        return this.request(url, 'GET');
    }


    POST(url, data, headers) {
        return this.request(url, 'POST', data, headers);
    }

    PUT(url, data, headers) {
        return this.request(url, 'PUT', data, headers);
    }

    DELETE(url) {
        return this.request(url, 'DELETE');
    }

    request(url, method, data, headers) {
        return fetch(url, {
            method: method,
            headers: headers,
            body: data,
        }).then(this.parse.bind(this)).catch(this.error.bind(this));
    }

    parse(res) {
        if (res.ok) {
            if (res.status === 204) {
                return {};
            }
            return res.json();
        } else {
            throw res.text();
        }
    }

    async error(err) {
        if (this.errorHandler) {
            this.errorHandler(await err);
            return;
        }
        alert(await err);
    }
}

export default API;