from bratlib.data import Entity


class ContigEntity(Entity):

    @property
    def start(self):
        return self.spans[0][0]

    @start.setter
    def start(self, value):
        self.spans[0] = value, self.spans[0][1]

    @property
    def end(self):
        return self.spans[-1][-1]

    @end.setter
    def end(self, value):
        self.spans[-1] = self.spans[-1][0], value
