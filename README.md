# __NGCmod__
## _Простой Python модуль для парсинга, изменения и сборки конфигурационных файлов Nginx_
### v1.0.1
----------------------
### __Установка__
Поддерживается Python версии 3.6+
Достаточно клонировать репозиторий и копировать папку `NGCmod` из репозитория в папку со своим рабочим проектом:
```sh
git clone https://github.com/vvpresents/NGCmod.git
cp -r NGCmod/NGCmod /home/user123/py_project1
```
### __Как использовать__
#### Особенности
NGCmod на данный момент поддерживает работу с __единственным файлом конфигурации (не обязательно основным)__, также модуль не подставляет содержимое других файлов в исходный, если среди директив Nginx в исходном файле есть `include ... ;`
NGCmod __не проверяет валидность__ файла конфигурации, предполагается что он уже проверен на валидность, например с помощью `nginx -t`
#### Функции модуля
После того, как модуль импортирован
```py
from NGCmod import NGCmod
```
доступны следующии функции:

__NGCmod.parse_conf()__ - c нее начинается инициализация файла конфигурации `nginx_conf_path_or_var`, после чего из него генерируются токены и список директив:
```py
tokenized_conf, directives_list = NGCmod.parse_conf(nginx_conf_path_or_var, encoding = 'utf-8', tab_to_whitespace = 4)
```
__NGCmod.build_conf()__ - собирает из токенизированной конфигурации строку с валидной конфигурацией Nginx, если исходный файл был валиден и не было допущено ошибок при его изменении:
```py
nginx_conf_string = NGCmod.build_conf(tokenized_conf, build_mode = 'minimal', indent_whitespaces_amount = 4, string_whitespaces_amount = 1)
```
__NGCmod.find_directives()__ - возвращает список найденных директив  в списке директив `directives_list`, параметры поиска которых указываются в списке `target_directive_search_options`:
```py
found_directives = NGCmod.find_directives( directives_list, target_directive_search_options)
```
__NGCmod.add_directives()__ - добаляет одну или несколько простых директив из списка `directives_and_arguments` Nginx перед, после, внутрь другой директивы, параметры которой которой указываются в списке `target_directives` - этот список должен содержать параметры одной директивы для однозначного определения позиции вставки новых директив. Функция возвращает токенизированную конфигурацию и список директив:
```py
new_tokenized_conf, new_directives_list = NGCmod.add_directives(tokenized_conf, directives_list, target_directives, where, directives_and_arguments)
```
__NGCmod.del_directives()__ - удаляет одну или несколько любых директив Nginx, параметры  которых указываются в списке `target_directives`.
Возвращает токенизированную конфигурацию и список директив:
```py
new_tokenized_conf, new_directives_list = NGCmod.del_directives(tokenized_conf, directives_list, target_directives, multi_dir_deletion_mode = True)
```
__NGCmod.get_directives_list_with_lines()__ - возвращает список директив `directives_list` с указанием реального местоположения в  файле конфигурации, которому соответствует токенизированная конфигурация `tokenized_conf`:
```py
directives_list_with_lines = NGCmod.get_directives_list_with_lines(tokenized_conf, directives_list)
```

### Примеры
Рассмотрим валидный конфигурационный файл Nginx c именем `test_server.conf`:
```sh
# cat /etc/nginx/sites-available/test_server.conf
```
```sh
server {
        listen  123.123.123.123:443 ssl;
        server_name     .film-club.com;

        ssl on;
        ssl_protocols   TLSv1 TLSv1.1 TLSv1.2;
        ssl_certificate /home/sys_user/tmp_ssl/0cinema-hd/film-club.com.crt;
        ssl_certificate_key     /home/sys_user/tmp_ssl/0cinema-hd/film-club.com.key;
        resolver 127.0.0.1;
        ssl_stapling on;

		ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256';

  ssl_prefer_server_ciphers on;
        ssl_dhparam /home/ru/d/ssl/dhparams.pem;

#        error_page 404  /.err/404.htm;
        error_page 403  /.err/403.htm;
#        error_page 401  /.err/401serv.htm;
        error_page 406 =500 /.err/service.htm;
        error_page 500  /.err/500.htm;
        error_page 502  /.err/500.htm;
        error_page 504  /.err/500.htm;
        
        index  index.html index.htm;

        location ^~ /.err {
            root /home/ru/d/lng/en;
            if ( $http_accept_language ~* "ru|ua|kz|by" ) {
                root /home/ru/d/lng/ru;
            }
        }
        root /home/ru/www;
        location / {
#return 406;

limit_except GET POST {
                deny all;
                }
            client_body_timeout 40;
            client_body_buffer_size 32k;
            client_max_body_size 40M;

            proxy_pass https://193.109.247.111;
            proxy_buffering off;
            proxy_redirect off;
            proxy_buffer_size 64k;
            proxy_buffers 4 32k;
            proxy_busy_buffers_size 64k;
            proxy_temp_file_write_size 64k;
            proxy_set_header   Host             $http_host;
            proxy_set_header   X-Forwarded-For  $remote_addr;
            proxy_set_header   XU-Forwarded-For  $remote_addr;
            proxy_set_header   X-Request-URI    $request_uri;
            proxy_read_timeout 30;
            proxy_intercept_errors off;
        }
        
        location = /old_auth_entry {
            return 401;
        }
}

```
Получим токены и список директив:
```py
nginx_conf_path = "/etc/nginx/sites-available/test_server.conf"
tokenized_conf, directives_list = NGCmod.parse_conf(nginx_conf_path)
```
Добавим директивы `access_log  off;` и `error_log   /var/log/test_error_log error;` в блочную директиву `server`:  
```py
found_dirs1 = NGCmod.find_directives(directives_list, [['main/', [] ], 'any', ['server', {'listen':[], 'server_name':['.film-club.com']}], 'any_server_name'])
tokenized_conf, directives_list = NGCmod.add_directives(tokenized_conf, directives_list, found_dirs1, 'into', [['simple', 'access_log', 'off'], ['simple', 'error_log', ' /var/log/test_error_log', 'error']])
```
Добавим директивы `server_name .film-club-vip100.com;` и `server_name .film-club-vip200.com;`  после директивы `server_name     .film-club.com;`:
```py
found_dirs2 = NGCmod.find_directives(directives_list, [['main/server/', [], [{'listen':[], 'server_name':['.film-club.com']}] ], 'any', ['server_name', '.film-club.com' ], 'any'])
tokenized_conf, directives_list = NGCmod.add_directives(tokenized_conf, directives_list, found_dirs2, 'after', [['simple', 'server_name', '.film-club-vip100.com'], ['simple', 'server_name', '.film-club-vip200.com']])
```
Удалим все директивы `location` в блочной директиве `server`:
```py
found_dirs3 = NGCmod.find_directives(directives_list, [['main/server/', [], [{'listen':[], 'server_name':['.film-club.com']}] ], 'any', ['location'], 'any'])
tokenized_conf, directives_list = NGCmod.del_directives(tokenized_conf, directives_list, found_dirs3)
```
Соберем нашу конфигурацию в строку, готовую для записи, и запишем ее в файл:
```py
builded = NGCmod.build_conf(tokenized_conf)
with open( '/tmp/NEW_test_server.conf', 'w') as f:
    f.write(builded)
```
Полученный файл:
```sh
# cat /tmp/NEW_test_server.conf
```
```sh
server {
    listen 123.123.123.123:443 ssl;
    server_name .film-club.com;
    server_name .film-club-vip100.com;
    server_name .film-club-vip200.com;
    ssl on;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_certificate /home/sys_user/tmp_ssl/0cinema-hd/film-club.com.crt;
    ssl_certificate_key /home/sys_user/tmp_ssl/0cinema-hd/film-club.com.key;
    resolver 127.0.0.1;
    ssl_stapling on;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_dhparam /home/ru/d/ssl/dhparams.pem;
    #        error_page 404  /.err/404.htm;
    error_page 403 /.err/403.htm;
    #        error_page 401  /.err/401serv.htm;
    error_page 406 =500 /.err/service.htm;
    error_page 500 /.err/500.htm;
    error_page 502 /.err/500.htm;
    error_page 504 /.err/500.htm;
    index index.html index.htm;
    root /home/ru/www;
    access_log off;
    error_log  /var/log/test_error_log error;
}
```
