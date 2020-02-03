import os
import dialogflow_v2beta1 as dialogflow

class DflowOperation():
    """
        DflowOperation holds methods for handling dialogflow agent
    """

    entity_list = {}
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'My First Project-2e1b0d351e36.json'

    def __init__(self, project_id):
        self.project_id = project_id
        self.list_update()

    def list_update(self):
        """
            Lists all entities under `project_id` and populates those values to class variable `entity_list`
        """

        DflowOperation.entity_list = {}

        client = dialogflow.EntityTypesClient()
        parent = client.project_agent_path(self.project_id)

        for element in list(client.list_entity_types(parent)):
            DflowOperation.entity_list[element.display_name] = element.name.split('/')[-1]

    def list_entity_types(self, entity_type, entity):
        """Gets entities under the given entity_type

        :param entity_type: name of entity type
        :type entity_type: str
        :param entity_type: name of entity for which the search needs to be done
        :type entity_type: str
        :return: empty list (or) list of entity synonyms
        :rtype: list
        """

        client = dialogflow.EntityTypesClient()
        parent = client.project_agent_path(self.project_id)

        for element in list(client.list_entity_types(parent)):
            if entity_type == element.display_name:
                for entry in element.entities:
                    if entity == entry.value:
                        return list(entry.synonyms)

        return []

    def update_category(self, entity_type):
        """Adding to @category entity.

        :param entity_type: name of entity type for which values have to be viewed
        :type entity_type: str
        """

        if 'category' in DflowOperation.entity_list:

            client = dialogflow.EntityTypesClient()
            parent = client.entity_type_path(self.project_id, DflowOperation.entity_list['category'])

            string = "@" + entity_type + ":" + entity_type
            entities = [
                {"value": string, "synonyms": [string]},
            ]

            response = client.batch_create_entities(parent, entities)

            self.list_update()

            print('Entity updated in @category entity!!')
        else:
            print('No @category entity found!!')

    def create_entity_type(self, path, kind='KIND_MAP'):
        """Create, configure, populate and upload new entity_type.

        :param path: Location of entity data
        :type path: str
        :param kind: type of entity_type. Either KIND_MAP(1) OR KIND_LIST(2)
        :type kind: str (or) int
        :return: method response
        :rtype: str
        """

        display_name = path.split('/')[-1].split('.')[0]

        def configure_entity_type():

            import csv
            import json

            reader = csv.reader(open(path))
            entity_type = {}
            entity_type = {'display_name': display_name, 'kind': kind, 'entities': []}
            for row in reader:
                entity = {}
                entity['value'] = row[0]
                entity['synonyms'] = [i for i in row[1:] if i != '']
                entity_type['entities'].append(entity)

            return entity_type

        entity_type = configure_entity_type()

        if display_name not in DflowOperation.entity_list:

            client = dialogflow.EntityTypesClient()
            parent = client.project_agent_path(self.project_id)

            client.create_entity_type(parent, entity_type)

            self.list_update()

            print('New Entity type created!!')
            if display_name != 'outer' and display_name != 'multi':
                self.update_category(display_name)
        else:
            print('Entity Type already exists!!')
            self.add_entities(display_name, entity_type['entities'])

    def add_entities(self, entity_type, entities):
        """Updates entity in entity_type

        :param entity_type: name of the entity to be updated
        :type entity_type: str
        :param entities: entity list to be added in entity_type
        :type entities: list
        """

        for i,entity in enumerate(entities):
            entities[i]['synonyms'] += self.list_entity_types(entity_type, entity['value'])

        client = dialogflow.EntityTypesClient()
        parent = client.entity_type_path(self.project_id, DflowOperation.entity_list[entity_type])

        response = client.batch_update_entities(parent, entities)

        self.list_update()

        print('Entity updated!!')