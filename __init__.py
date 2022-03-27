# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# All credits go to domcross (Github https://github.com/domcross)

import time

from mycroft.messagebus.message import Message
from mycroft.skills.core import MycroftSkill, intent_handler, intent_file_handler
from adapt.intent import IntentBuilder
from mycroft.util.log import LOG, getLogger
import subprocess
import time

from pixel_ring import pixel_ring
from gpiozero import LED

LOGGER = getLogger(__name__)

class ReSpeaker_4mic_hat(MycroftSkill):

	def __init__(self):
		super(ReSpeaker_4mic_hat, self).__init__(name="ReSpeaker_4mic_hat")
		self.pattern = "echo"
		self.proc = None
		self.button_pin = 0

	def initialize(self):
		self.button_pin = self.settings.get("gpio", "26")
		self.pattern = self.settings.get("pattern", "echo")
		self.log.info("Pixel Ring: Initializing")
		self.power = LED(5)
		self.power.on()
		pixel_ring.set_brightness(10)
		pixel_ring.change_pattern(self.pattern)
		pixel_ring.wakeup()
		self.enable()
		self._start()

	def on_websettings_changed(self):
		"""Callback triggered anytime Skill settings are modified on backend."""
		self._stop()
		self.button_pin = self.settings.get("gpio", "26")
		self._start()

	def _check_gpio_changed(self):
        # check if the gpio pin has changed
        if self.settings.get("station") != self.button_pin:
            LOGGER.info("GPIO pin changed")
            # restart button.py with the new pin assigned
            self._stop()
            time.sleep(2)  # chose an arbitrary value
            self.button_pin = self.settings.get("gpio", "26")
            self.start()

	def enable(self):
		self.log.info("Pixel Ring: Enabling")

		self.add_event('recognizer_loop:wakeword',
				self.handle_listener_wakeup)
		self.add_event('recognizer_loop:record_end',
				self.handle_listener_off)

		self.add_event('mycroft.skill.handler.start',
				self.handle_listener_think)
		self.add_event('mycroft.skill.handler.complete',
				self.handle_listener_off)

		self.add_event('recognizer_loop:audio_output_start',
				self.handler_listener_speak)
		self.add_event('recognizer_loop:audio_output_end',
				self.handle_listener_off)

		pixel_ring.off()

	def disable(self):
		self.log.info("Pixel Ring: Disabling")
		self.remove_event('recognizer_loop:wakeup')
		self.remove_event('recognizer_loop:record_end')
		self.remove_event('recognizer_loop:audio_output_start')
		self.remove_event('recognizer_loop:audio_output_end')
		self.remove_event('mycroft.skill.handler.start')
		self.remove_event('mycroft.skill.handler.complete')

	def shutdown(self):
		self.log.info("Pixel Ring: Shutdown")
		pixel_ring.off()
		self.power.off()
        # shutdown the button.py process
		self._stop()
		super(ReSpeaker_4mic_hat, self).shutdown()

	def handle_listener_wakeup(self, message):
		self.log.info("Pixel Ring: Wakeup")
		pixel_ring.listen()

	def handle_listener_off(self, message):
		self.log.info("Pixel Ring: Off")
		pixel_ring.off()

	def handle_listener_think(self, message):
		self.log.info("Pixel Ring: Think")
		pixel_ring.think()

	def handler_listener_speak(self, message):
		self.log.info("Pixel Ring: Speak")
		pixel_ring.speak()

	def _start(self):
        self.proc = subprocess.Popen(['python', self.root_dir + '/button.py', self.button_pin])
        LOGGER.info('button process pid = ' + str(self.proc.pid))
    
	def _stop(self):
        self.proc.kill()
        LOGGER.info('Shutting down button.py')
        		
	@intent_handler(IntentBuilder("").require("EnablePixelRing"))
	def handle_enable_pixel_ring_intent(self, message):
		self.enable()
		self.speak_dialog("EnablePixelRing")

	@intent_handler(IntentBuilder("").require("DisablePixelRing"))
	def handle_disable_pixel_ring_intent(self, message):
		self.disable()
		self.speak_dialog("DisablePixelRing")

def create_skill():
	return ReSpeaker_4mic_hat()
