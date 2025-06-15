class EventScheduler:
    def __init__(self):
        self.events = []
        self.current_time = 0

    def schedule_event(self, time, event_type, data):
        self.events.append({'time': time, 'event_type': event_type, 'data': data})
        self.events.sort(key=lambda x: x['time'])

    def get_next_events(self):
        current_events = []
        while self.events and self.events[0]['time'] <= self.current_time:
            current_events.append(self.events.pop(0))
        return current_events

    def advance(self):
        self.current_time += 1
