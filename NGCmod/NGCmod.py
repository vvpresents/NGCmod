from . parser import *

#  target_directive_search_options должен быть списком вида: [ context_path_and_id, context_id_check_type, directive_and_arguments, args_check_type ]
def find_directives(directives_list, target_directive_search_options):
    found_directives =  []
    # print('DIR_LIST', directives_list)
    i,j,k = 0,0,0
    len_directive_list = len(directives_list)
    context_path_and_id, context_id_check_type, directive_and_arguments, args_check_type = target_directive_search_options
    directive, arguments = directive_and_arguments[0], directive_and_arguments[1:]
    while i < len_directive_list:
        curr_directive = directives_list[i]
        args_matched = False
        if curr_directive[3] == directive:
            if not arguments:
                args_matched = True
            elif (directive != 'server'):
                cur_dir_args = curr_directive[4:]
                any_arg, all_args = False, True
                for arg in arguments :
                    if arg in cur_dir_args: 
                        any_arg = True
                    else: 
                        all_args = False
                if (args_check_type == 'any' and any_arg) or (args_check_type == 'all' and all_args):
                    args_matched = True
            elif directive == 'server':
                curr_server_directive_id = get_server_directive_id(i, directives_list)
                # print('CURR_SERV_ID ====', curr_server_directive_id)
                any_listen, all_listen, any_server_name, all_server_name = None, None, None, None
                if arguments[0]['listen']:
                    any_listen, all_listen = False, True
                    for arg in arguments[0]['listen']:
                        if arg in curr_server_directive_id['listen']:
                            any_listen = True
                        else:
                            all_listen = False
                if arguments[0]['server_name']:
                    any_server_name, all_server_name = False, True
                    for arg in arguments[0]['server_name']:
                        if arg in curr_server_directive_id['server_name']:
                            any_server_name = True
                        else:
                            all_server_name = False
                if ( (args_check_type == 'any_listen' and any_listen == True) 
                or (args_check_type == 'all_listen' and all_listen == True)
                or (args_check_type == 'any_server_name' and any_server_name == True)
                or (args_check_type == 'all_server_name' and all_server_name == True) 
                or (args_check_type == 'any_listen_and_server_name' and any_listen == True and any_server_name == True)
                or (args_check_type == 'all_listen_and_server_name' and all_listen == True and all_server_name == True) ):
                    args_matched = True
        if  args_matched and context_path_and_id: # проверили аргументы,  можно проверять контекст
            # print("ARGS_MATCHED = ", args_matched)
            j = i - 1
            block_dir_found_amount, curr_context_path_reversed, curr_context_id_reversed = 0, [], []
            curr_context = ['main/', []]  # результат должен быть примерно таким: ['main/http/server/location/', [], [], [{'listen': ['80'], 'server_name': ['domain2.com', 'www.domain2.com']}], ['~*']]
            while (j >= 0):
                if directives_list[j][2] == 'block' and is_subrange(curr_directive[0], curr_directive[1], directives_list[j][0], directives_list[j][1]):
                    block_dir_found_amount += 1
                    curr_context_path_reversed.append( directives_list[j][3] )
                    if directives_list[j][3] != 'server':
                        curr_context_id_reversed.append( directives_list[j][4:] )
                    else:
                        curr_context_id_reversed.append( [get_server_directive_id(j, directives_list)] )
                j -= 1
            # print('block_dir_found_amount, curr_context_path_reversed, curr_context_id_reversed = ', block_dir_found_amount, curr_context_path_reversed, curr_context_id_reversed)
            for k in range(block_dir_found_amount - 1, -1, -1):
                curr_context[0] += curr_context_path_reversed[k] + '/'
                curr_context.append( curr_context_id_reversed[k] )
            # print('curr_context =', curr_context)
            if curr_context[0] == context_path_and_id[0]:
                if (context_id_check_type == 'none'):
                    found_directives.append(curr_directive[:])
                else:
                    # print('LEN =', len(curr_context), len(context_path_and_id))
                    context_id_check_list = [ {} for x in range (block_dir_found_amount + 2)] 
                    for k in range(1, block_dir_found_amount + 2):
                        # print(curr_context[k], context_path_and_id[k])
                        if curr_context[k] != context_path_and_id[k]:
                            if curr_context[k] and context_path_and_id[k]: # оба не пустые списки
                                if type(curr_context[k][0]) == dict:
                                    any_listen = any(arg in curr_context[k][0]['listen'] for arg in context_path_and_id[k][0]['listen'] )
                                    any_server_name = any(arg in curr_context[k][0]['server_name'] for arg in context_path_and_id[k][0]['server_name'] )
                                    context_id_check_list[k]['any_listen'] = any_listen
                                    context_id_check_list[k]['any_server_name'] = any_server_name
                                else:
                                    any_arg = any(arg in curr_context[k] for arg in context_path_and_id[k])
                                    context_id_check_list[k]['any_arg'] = any_arg
                            else:
                                context_id_check_list[k]['checked'] = False
                        else:
                            context_id_check_list[k]['checked'] = True
                    # print(context_id_check_list)
                    context_id_matched = True
                    if context_id_check_type == 'any':
                        for k in range(1, block_dir_found_amount + 2):
                            if  ( context_id_check_list[k].get('checked') == False   
                            or  ( context_id_check_list[k].get('any_listen') == False
                              and context_id_check_list[k].get('any_server_name') == False ) ):
                                context_id_matched = False
                    elif  context_id_check_type == 'any_arg_any_listen_and_server_name':
                        for k in range(1, block_dir_found_amount + 2):
                            if  ( context_id_check_list[k].get('checked') == False   
                            or  ( context_id_check_list[k].get('any_listen') == False
                              or context_id_check_list[k].get('any_server_name') == False ) ):
                                context_id_matched = False
                    # print(context_id_matched, curr_directive )
                    if context_id_matched:
                        found_directives.append(curr_directive[:])
        i += 1
    # print('DIRECTIVE POS=', found_directives)
    return found_directives   

def add_directives (tokenized_conf, directives_list, target_directives, where, directives_and_arguments): # пример списка directives_and_arguments: [['simple', 'server_name', 'abc.ru', ...], ... ['block', 'location', '=', '/news.html'], ...]
    new_tokenized_conf = []
    # target_directives = find_directives(directives_list, target_directive_search_options)
    len_target_directives = len(target_directives)
    if len_target_directives == 1:
        i,k = 0,0
        dir_not_added = True
        target_directive_start, target_directive_end, target_directive_type = target_directives[0][0], target_directives[0][1], target_directives[0][2]
        target_dir_start_line_number, target_dir_end_line_number = tokenized_conf[target_directive_start][0], tokenized_conf[target_directive_end][0]
        first_directive_type = directives_and_arguments[0][0]
        len_directives_and_arguments = len(directives_and_arguments)
        if where == 'after':
            if first_directive_type == 'block':
                pass
            else:
                while i < len(tokenized_conf):
                    if  i != target_directive_end:
                        if dir_not_added:
                            new_tokenized_conf.append(tokenized_conf[i][:])
                        else:
                            new_tokenized_conf.append( [tokenized_conf[i][0] + len_directives_and_arguments, tokenized_conf[i][1]] )
                    else:
                        new_tokenized_conf.append(tokenized_conf[i][:])
                        for j in range(len_directives_and_arguments):
                            for dir_arg in directives_and_arguments[j][1:]:
                                new_tokenized_conf.append([target_dir_end_line_number + 1 + j, dir_arg])
                            new_tokenized_conf.append([target_dir_end_line_number + 1 + j, ';'])
                        dir_not_added = False
                    i += 1
        elif where == 'before':
            if first_directive_type == 'block':
                pass
            else:
                while i < len(tokenized_conf):
                    if  i != target_directive_start:
                        if dir_not_added:
                            new_tokenized_conf.append(tokenized_conf[i][:])
                        else:
                            new_tokenized_conf.append( [tokenized_conf[i][0] + len_directives_and_arguments, tokenized_conf[i][1]])
                    else:
                        for j in range(len_directives_and_arguments):
                            for dir_arg in directives_and_arguments[j][1:]:
                                new_tokenized_conf.append([target_dir_start_line_number + j, dir_arg])
                            new_tokenized_conf.append([target_dir_start_line_number + j , ';'])
                        new_tokenized_conf.append( [tokenized_conf[i][0] + len_directives_and_arguments, tokenized_conf[i][1] ] )
                        dir_not_added = False
                    i += 1
        elif where == 'into' and target_directive_type == 'block':
            if first_directive_type == 'block':
                pass
            else:
                while i < len(tokenized_conf):
                    if  i != target_directive_end:
                        if dir_not_added:
                            new_tokenized_conf.append(tokenized_conf[i][:])
                        else:
                            new_tokenized_conf.append( [tokenized_conf[i][0] + len_directives_and_arguments, tokenized_conf[i][1] ])
                    else:
                        for j in range(len_directives_and_arguments):
                            for dir_arg in directives_and_arguments[j][1:]:
                                new_tokenized_conf.append([target_dir_end_line_number + j, dir_arg])
                            new_tokenized_conf.append([target_dir_end_line_number + j, ';'])
                        new_tokenized_conf.append( [tokenized_conf[i][0] + len_directives_and_arguments, tokenized_conf[i][1] ] )
                        dir_not_added = False
                    i += 1
        elif where == 'into' and target_directive_type != 'block':
            print("[add_directives] ERROR: Can't add directive into non-block directive.")
            return [], []
        return new_tokenized_conf, get_directives_list(new_tokenized_conf)
    elif len_target_directives == 0:
        print("[add_directives] ERROR: No directives found matching the specified conditions.")
        return [], []
    else:
        print("[add_directives] ERROR: Found 2 or more directives matching specified conditions.")
        return [], []

def del_directives (tokenized_conf, directives_list, target_directives, multi_dir_deletion_mode = True):
    new_tokenized_conf = []
    i = 0
    # target_directives = find_directives(directives_list, target_directive_search_options)
    len_target_directives = len(target_directives)
    if (multi_dir_deletion_mode and len_target_directives > 0) or (not multi_dir_deletion_mode and len_target_directives == 1 ) :
        j = 0
        target_directive_start, target_directive_end = target_directives[j][0], target_directives[j][1]
        lines_amount = tokenized_conf[target_directive_end][0] - tokenized_conf[target_directive_start][0] + 1 
        while i < len(tokenized_conf):
            if  i < target_directive_start:
                new_tokenized_conf.append(tokenized_conf[i][:])
            elif  i > target_directive_end :
                # if j+1 < len_target_directives and i != target_directives[j+1][0]:
                #     new_tokenized_conf.append( [tokenized_conf[i][0] - lines_amount, tokenized_conf[i][1] ])
                if j+1 < len_target_directives and i == target_directives[j+1][0]:
                    target_directive_end = target_directives[j+1][1]
                    lines_amount += tokenized_conf[target_directives[j+1][1]][0] - tokenized_conf[target_directives[j+1][0]][0] + 1 
                    j += 1
                else:
                    new_tokenized_conf.append( [tokenized_conf[i][0] - lines_amount, tokenized_conf[i][1] ])
            i += 1
        return new_tokenized_conf, get_directives_list(new_tokenized_conf)
    elif not multi_dir_deletion_mode and len_target_directives > 1:
        print("[del_directives] ERROR: Found 2 or more directives matching specified conditions.")
        return [], []
    elif len_target_directives == 0:
        print("[del_directives] ERROR: No directives found matching the specified conditions.")
        return [], []  
        
def parse_conf(nginx_conf_path_or_var, encoding = 'utf-8', tab_to_whitespace = 4):
    nginx_conf = init_nginx_conf(nginx_conf_path_or_var, encoding)
    quoting_ranges, delimiters_with_pos = get_quoting_ranges_and_delimiters(nginx_conf, tab_to_whitespace = tab_to_whitespace)
    unq_delimiters_with_pos = get_unquoted_delimiters(quoting_ranges, delimiters_with_pos)
    final_delimiters_with_pos = get_final_delimiters(nginx_conf, unq_delimiters_with_pos)
    tokenized_conf = tokenize_nginx_conf( nginx_conf, final_delimiters_with_pos)
    directives_list = get_directives_list(tokenized_conf)
    return tokenized_conf, directives_list

def build_conf(tokenized_conf, build_mode = 'minimal', indent_whitespaces_amount = 4, string_whitespaces_amount = 1):
    if build_mode == 'minimal':
        return build_nginx_conf_minimal(tokenized_conf, indent_whitespaces_amount, string_whitespaces_amount)

def get_directives_list_with_lines(tokenized_conf, directives_list):
    dir_list_with_lines = []
    for directive in directives_list:
        dir_list_with_lines.append( [tokenized_conf[directive[0]][0], tokenized_conf[directive[1]][0]] + directive[2:] )
    return dir_list_with_lines

# def find_directives_with_pos (tokenized_conf, directives_list, target_directive_search_options):
#     dirs_with_pos = []
#     found_dirs = find_directives(directives_list, target_directive_search_options)
#     # for directive in found_dirs:
#     #     directive[0] = tokenized_conf[directive[0]][0]
#     #     directive[1] = tokenized_conf[directive[1]][0]
#     # return found_dirs
#     for directive in found_dirs:
#         dirs_with_pos.append( [tokenized_conf[directive[0]][0], tokenized_conf[directive[1]][0]] + directive[2:])
#     return dirs_with_pos
    
