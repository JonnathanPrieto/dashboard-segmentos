print(f'{len(seg)} filas en segmentacion.json')
    else:
        print('Vista no encontrada')
        with open('data/segmentacion.json', 'w') as f:
            json.dump([], f)

    print('Buscando Transiciones de segmentos Total...')
    trans_id = get_view_id(token, 'Transiciones de segmentos Total')
    if trans_id:
        trans = get_table_data(token, trans_id)
        with open('data/transiciones.json', 'w', encoding='utf-8') as f:
            json.dump(trans, f, ensure_ascii=False, indent=2)
        print(f'{len(trans)} filas en transiciones.json')
    else:
        print('Vista no encontrada')
        with open('data/transiciones.json', 'w') as f:
            json.dump([], f)

if __name__ == '__main__':
    main()
