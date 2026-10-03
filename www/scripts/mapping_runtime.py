"""Pure input-matching rules shared by parsing, rendering and coverage checks."""


def normalize_input(key):
    return key[4:] if key.startswith(('Neg_', 'Pos_')) else key


def matches_input(mapped_key, input_key):
    """A full axis covers both directions; a half-axis only covers itself."""
    if mapped_key.startswith(('Neg_', 'Pos_')):
        return mapped_key == input_key
    return mapped_key == normalize_input(input_key)


def missing_inputs(mapping, keys):
    mapped = [row.get('joy', '') for box in mapping.get('boxes', [])
              for row in box.get('rows', []) if row.get('joy')]
    return sorted(key for key in set(keys)
                  if not any(matches_input(candidate, key) for candidate in mapped))


def used_inputs(physical_keys, modifiers, device_ids, device_index):
    """Include modifier-only buttons as well as ordinary bound actions."""
    used = {control.get('InputKey', pk['Key'])
            for pk in physical_keys.values()
            if pk['Device'] in device_ids and int(pk['DeviceIndex']) == device_index
            for bind in pk.get('Binds', {}).values()
            for control in bind.get('Controls', {}).values()}
    for entries in modifiers.values():
        for modifier in entries:
            if (modifier.get('Device') in device_ids and
                    int(modifier.get('DeviceIndex', 0)) == device_index and
                    modifier.get('Key') and modifier['Key'] != 'HOLD'):
                used.add(modifier['Key'])
    return used


def mapping_software_warning(devices):
    if not any(key.split('::')[0] == 'ThrustMasterWarthogCombined' for key in devices):
        return ''
    return ('<h2>Virtual Warthog device detected</h2>'
            'This bindings file refers to a combined virtual Warthog device, '
            'commonly created by Thrustmaster TARGET. This does not establish '
            'which software is currently running. If controls are missing, '
            'check the virtual-device mapping and the in-game bindings.')
