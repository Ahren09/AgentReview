"""
BASELINE: The default settings which all other settings compare against.

"""

baseline_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "BASELINE",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

benign_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "benign",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

malicious_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "malicious",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

unknowledgeable_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "knowledgeable",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

knowledgeable_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "knowledgeable",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}


responsible_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "responsible",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

irresponsible_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "irresponsible",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

conformist_ACx1_setting = {
    "AC": [
        "conformist"
    ],

    "reviewer": [
        "BASELINE",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

authoritarian_ACx1_setting = {
    "AC": [
        "authoritarian"
    ],

    "reviewer": [
        "BASELINE",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

inclusive_ACx1_setting = {
    "AC": [
        "inclusive"
    ],

    "reviewer": [
        "BASELINE",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}



no_numeric_ratings_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": [],
        "persons_aware_of_authors_identities": []
    }
}

malicious_and_irresponsible_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "malicious irresponsible",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}


# All experimental settings.
# Customize your own by adding new settings to this dict.
all_settings = {
    "BASELINE": baseline_setting,
    "benign_Rx1": benign_Rx1_setting,
    "malicious_Rx1": malicious_Rx1_setting,
    "knowledgeable_Rx1": knowledgeable_Rx1_setting,
    "unknowledgeable_Rx1": unknowledgeable_Rx1_setting,
    "responsible_Rx1": responsible_Rx1_setting,
    "irresponsible_Rx1": irresponsible_Rx1_setting,
    "conformist_ACx1": conformist_ACx1_setting,
    "authoritarian_ACx1": authoritarian_ACx1_setting,
    "inclusive_ACx1": inclusive_ACx1_setting,
    "no_numeric_ratings": no_numeric_ratings_setting,
    "malicious_and_irresponsible_Rx1": malicious_and_irresponsible_Rx1_setting,

}

