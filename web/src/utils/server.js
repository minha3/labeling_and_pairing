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

    get_images(fileId) {
        return this.GET(`${this.apibase}/images?file_id=${fileId}`)
    }

    get_image(imageId) {
        return this.GET(`${this.apibase}/images/${imageId}`)
    }

    get_image_url(imageId) {
        return`${this.apibase}/images/${imageId}`
    }

    get_bboxes_from_file(fileId, filters, page=1, items_per_page=-1) {
        return this.GET(`${this.apibase}/bboxes?file_id=${fileId}&page=${page}&items_per_page=${items_per_page}${this.join_param({'filters': filters})}`)
    }

    update_label(labelId, data) {
        const headers = new Headers();
        headers.append('Content-Type', 'application/json');
        return this.PUT(`${this.apibase}/labels/${labelId}`, JSON.stringify(data), headers)
    }

    get_label_statistics(fileId, filters) {
        return this.GET(`${this.apibase}/labels/statistics?file_id=${fileId}${this.join_param({'filters': filters})}`)
    }

    export(fileId, filters) {
        return this.POST(`${this.apibase}/exports?file_id=${fileId}${this.join_param({'filters': filters})}`)
    }
}

export default Server