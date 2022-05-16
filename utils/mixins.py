# pylint: disable=useless-object-inheritance
# pylint: disable=consider-using-f-string
class ModelMixin(object):
    "model mixin"
    __slots__ = ()

    def to_dict(self, excludes: tuple = None, selects: tuple = None):
        if not hasattr(self, '_meta'):
            raise TypeError('<%r> does not a django.db.models.Model object.' %
                            self)
        if selects:
            return {f: getattr(self, f) for f in selects}
        if excludes:
            return {
                f.attname: getattr(self, f.attname)
                for f in self._meta.fields if f.attname not in excludes
            }
        return {f.attname: getattr(self, f.attname) for f in self._meta.fields}

    def update_by_dict(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.save()
