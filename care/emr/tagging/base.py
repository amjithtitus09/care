from care.emr.models.tag_config import TagConfig
from care.emr.resources.tag.config_spec import TagConfigReadSpec


class BaseTagManager:
    def set_tag(self, resource_type, resource, tag_instance, user):
        pass

    def set_tags(self, resource_type, resource, tag_instances, user):
        for i in tag_instances:
            self.set_tag(resource_type, resource, i, user)

    def render_tags(self, resource, *args, **kwargs):
        pass

    def unset_tag(self, resource, tag_instance, user):
        pass

    def unset_tags(self, resource, tag_instances, user):
        for i in tag_instances:
            self.unset_tag(resource, i, user)

    def get_tag_config_object(self, tag_id):
        # TODO: Add cache
        return TagConfig.objects.filter(id=tag_id).first()

    def get_tag_from_external_id(self, external_id):
        return TagConfig.objects.filter(external_id=external_id).first()


class SingleFacilityTagManager(BaseTagManager):
    def get_resource_tag(self, resource):
        return resource.tags or []

    def get_tag_qs(self, tag_ids, resource_type):
        return TagConfig.objects.filter(external_id__in=tag_ids, resource=resource_type)

    def set_tag(self, resource_type, resource, tag_instance, user):
        # AuthZ pending
        # Attain Tag lock for resource id
        tags = self.get_resource_tag(resource)
        tag_instance = TagConfig.objects.filter(external_id=tag_instance).first()
        if not tag_instance:
            return
        if tag_instance.id in tags:
            raise ValueError("Tag already set")
        if tag_instance.resource != resource_type:
            raise ValueError("Tag resource does not match resource type")
        if (
            tag_instance.root_tag_config
            and TagConfig.objects.filter(
                id__in=tags, root_tag_config=tag_instance.root_tag_config
            ).exists()
        ):
            raise ValueError("Tag Parent is already set")
        tags.append(tag_instance.id)
        resource.tags = tags
        resource.save(update_fields=["tags"])

    def unset_tag(self, resource, tag_instance, user):
        tags = self.get_resource_tag(resource)
        if tag_instance.id not in tags:
            raise ValueError("Tag not set")
        tags.remove(tag_instance.id)
        resource.tags = tags
        resource.save(update_fields=["tags"])

    def render_tags(self, resource, *args, **kwargs):
        tags = self.get_resource_tag(resource)
        rendered_tags = []
        for tag in tags:
            tag_obj = self.get_tag_config_object(tag)
            if tag_obj:
                rendered_tags.append(TagConfigReadSpec.serialize(tag_obj).to_json())
        return rendered_tags


class MultiFacilityTagManager(BaseTagManager):
    pass
