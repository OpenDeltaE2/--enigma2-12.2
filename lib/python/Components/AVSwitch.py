from config import config, ConfigSlider, ConfigSelection, ConfigYesNo, ConfigEnableDisable, ConfigSubsection, ConfigBoolean, ConfigSelectionNumber, ConfigNothing, NoSave
from enigma import eAVSwitch, eDVBVolumecontrol, getDesktop
from SystemInfo import SystemInfo
from Tools.Directories import fileExists
import os
from boxbranding import getBoxType
boxtype = getBoxType()

class AVSwitch:
	def setInput(self, input):
		INPUT = {"ENCODER": 0, "SCART": 1, "AUX": 2}
		eAVSwitch.getInstance().setInput(INPUT[input])

	def setColorFormat(self, value):
		eAVSwitch.getInstance().setColorFormat(value)

	def setAspectRatio(self, value):
		eAVSwitch.getInstance().setAspectRatio(value)

	def setSystem(self, value):
		eAVSwitch.getInstance().setVideomode(value)

	def getOutputAspect(self):
		valstr = config.av.aspectratio.value
		if valstr in ("4_3_letterbox", "4_3_panscan"): # 4:3
			return (4, 3)
		elif valstr == "16_9": # auto ... 4:3 or 16:9
			if fileExists("/proc/stb/vmpeg/0/aspect"):
				with open("/proc/stb/vmpeg/0/aspect", "r") as f:
					if "1" in f.read():
						return (4,3)
		elif valstr in ("16_9_always", "16_9_letterbox"): # 16:9
			pass
		elif valstr in ("16_10_letterbox", "16_10_panscan"): # 16:10
			return (16, 10)
		return (16, 9)

	def getFramebufferScale(self):
		aspect = self.getOutputAspect()
		fb_size = getDesktop(0).size()
		return (aspect[0] * fb_size.height(), aspect[1] * fb_size.width())

	def getAspectRatioSetting(self):
		valstr = config.av.aspectratio.value
		if valstr == "4_3_letterbox":
			val = 0
		elif valstr == "4_3_panscan":
			val = 1
		elif valstr == "16_9":
			val = 2
		elif valstr == "16_9_always":
			val = 3
		elif valstr == "16_10_letterbox":
			val = 4
		elif valstr == "16_10_panscan":
			val = 5
		elif valstr == "16_9_letterbox":
			val = 6
		return val

	def setAspectWSS(self, aspect=None):
		if not config.av.wss.value:
			value = 2 # auto(4:3_off)
		else:
			value = 1 # auto
		eAVSwitch.getInstance().setWSS(value)


def InitAVSwitch():
	config.av = ConfigSubsection()
	config.av.yuvenabled = ConfigBoolean(default=True)
	colorformat_choices = {"cvbs": "CVBS"}

	# when YUV, Scart or S-Video is not support by HW, don't let the user select it
	if SystemInfo["HasYPbPr"]:
		colorformat_choices["yuv"] = "YPbPr"
	if SystemInfo["HasScart"]:
		colorformat_choices["rgb"] = "RGB"
	if SystemInfo["HasSVideo"]:
		colorformat_choices["svideo"] = "S-Video"

	config.av.colorformat = ConfigSelection(choices=colorformat_choices, default="cvbs")
	config.av.aspectratio = ConfigSelection(choices={
			"4_3_letterbox": _("4:3 Letterbox"),
			"4_3_panscan": _("4:3 PanScan"),
			"16_9": "16:9",
			"16_9_always": _("16:9 always"),
			"16_10_letterbox": _("16:10 Letterbox"),
			"16_10_panscan": _("16:10 PanScan"),
			"16_9_letterbox": _("16:9 Letterbox")},
			default="16_9")
	config.av.aspect = ConfigSelection(choices={
			"4_3": "4:3",
			"16_9": "16:9",
			"16_10": "16:10",
			"auto": _("automatic")},
			default="auto")
	policy2_choices = {
	# TRANSLATORS: (aspect ratio policy: black bars on top/bottom) in doubt, keep english term.
	"letterbox": _("Letterbox"),
	# TRANSLATORS: (aspect ratio policy: cropped content on left/right) in doubt, keep english term
	"panscan": _("Pan&scan"),
	# TRANSLATORS: (aspect ratio policy: scale as close to fullscreen as possible)
	"scale": _("Just scale")}
	if fileExists("/proc/stb/video/policy2_choices"):
		with open("/proc/stb/video/policy2_choices") as f:
			if "full" in f.read():
				# TRANSLATORS: (aspect ratio policy: display as fullscreen, even if the content aspect ratio does not match the screen ratio)
				policy2_choices.update({"full": _("Full screen")})
			elif "auto" in f.read():
				# TRANSLATORS: (aspect ratio policy: automatically select the best aspect ratio mode)
				policy2_choices.update({"auto": _("Auto")})
	config.av.policy_169 = ConfigSelection(choices=policy2_choices, default="letterbox")
	policy_choices = {
	# TRANSLATORS: (aspect ratio policy: black bars on left/right) in doubt, keep english term.
	"pillarbox": _("Pillarbox"),
	# TRANSLATORS: (aspect ratio policy: cropped content on left/right) in doubt, keep english term
	"panscan": _("Pan&scan"),
	# TRANSLATORS: (aspect ratio policy: scale as close to fullscreen as possible)
	"scale": _("Just scale")}
	if fileExists("/proc/stb/video/policy_choices"):
		with open("/proc/stb/video/policy_choices") as f:
			if "nonlinear" in f.read():
				# TRANSLATORS: (aspect ratio policy: display as fullscreen, with stretching the left/right)
				policy_choices.update({"nonlinear": _("Nonlinear")})
			elif "full" in f.read():
				# TRANSLATORS: (aspect ratio policy: display as fullscreen, even if the content aspect ratio does not match the screen ratio)
				policy_choices.update({"full": _("Full screen")})
			elif "auto" in f.read():
				# TRANSLATORS: (aspect ratio policy: automatically select the best aspect ratio mode)
				policy_choices.update({"auto": _("Auto")})
	config.av.policy_43 = ConfigSelection(choices=policy_choices, default="pillarbox")
	config.av.tvsystem = ConfigSelection(choices={"pal": "PAL", "ntsc": "NTSC", "multinorm": "multinorm"}, default="pal")
	config.av.wss = ConfigEnableDisable(default=True)
	config.av.generalAC3delay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
	config.av.generalPCMdelay = ConfigSelectionNumber(-1000, 1000, 5, default=0)
	config.av.vcrswitch = ConfigEnableDisable(default=False)

	iAVSwitch = AVSwitch()

	def setColorFormat(configElement):
		map = {"cvbs": 0, "rgb": 1, "svideo": 2, "yuv": 3}
		iAVSwitch.setColorFormat(map[configElement.value])

	def setAspectRatio(configElement):
		map = {"4_3_letterbox": 0, "4_3_panscan": 1, "16_9": 2, "16_9_always": 3, "16_10_letterbox": 4, "16_10_panscan": 5, "16_9_letterbox": 6}
		iAVSwitch.setAspectRatio(map[configElement.value])

	def setSystem(configElement):
		map = {"pal": 0, "ntsc": 1, "multinorm": 2}
		iAVSwitch.setSystem(map[configElement.value])

	def setWSS(configElement):
		iAVSwitch.setAspectWSS()

	# this will call the "setup-val" initial
	config.av.colorformat.addNotifier(setColorFormat)
	config.av.aspectratio.addNotifier(setAspectRatio)
	config.av.tvsystem.addNotifier(setSystem)
	config.av.wss.addNotifier(setWSS)

	iAVSwitch.setInput("ENCODER") # init on startup
	SystemInfo["ScartSwitch"] = eAVSwitch.getInstance().haveScartSwitch()

	if SystemInfo["CanDownmixAC3"]:
		def setAC3Downmix(configElement):
			with open("/proc/stb/audio/ac3", "w") as f:
				if SystemInfo["DreamBoxAudio"]:
					f.write(configElement.value)
				else:
					f.write(configElement.value and "downmix" or "passthrough")
		if SystemInfo["DreamBoxAudio"]:
			choice_list = [("downmix", _("Downmix")), ("passthrough", _("Passthrough")), ("multichannel", _("convert to multi-channel PCM")), ("hdmi_best", _("use best / controlled by HDMI"))]
			config.av.downmix_ac3 = ConfigSelection(choices=choice_list, default="downmix")
		else:
			config.av.downmix_ac3 = ConfigYesNo(default=True)
		config.av.downmix_ac3.addNotifier(setAC3Downmix)

	if SystemInfo["CanAC3plusTranscode"]:
		def setAC3plusTranscode(configElement):
			with open("/proc/stb/audio/ac3plus", "w") as f:
				f.write(configElement.value)
		if SystemInfo["DreamBoxAudio"]:
			choice_list = [("use_hdmi_caps", _("controlled by HDMI")), ("force_ac3", _("convert to AC3")), ("multichannel", _("convert to multi-channel PCM")), ("hdmi_best", _("use best / controlled by HDMI")), ("force_ddp", _("force AC3plus"))]
			config.av.transcodeac3plus = ConfigSelection(choices=choice_list, default="force_ac3")
		else:
			choice_list = [("use_hdmi_caps", _("controlled by HDMI")), ("force_ac3", _("convert to AC3"))]
			config.av.transcodeac3plus = ConfigSelection(choices=choice_list, default="force_ac3")
		config.av.transcodeac3plus.addNotifier(setAC3plusTranscode)

	if SystemInfo["CanDownmixDTS"]:
		def setDTSDownmix(configElement):
			with open("/proc/stb/audio/dts", "w") as f:
				f.write(configElement.value and "downmix" or "passthrough")
		config.av.downmix_dts = ConfigYesNo(default=True)
		config.av.downmix_dts.addNotifier(setDTSDownmix)

	if SystemInfo["CanDTSHD"]:
		def setDTSHD(configElement):
			with open("/proc/stb/audio/dtshd", "w") as f:
				f.write(configElement.value)
		if boxtype in ("dm7080", "dm820"):
			choice_list = [("use_hdmi_caps", _("controlled by HDMI")), ("force_dts", _("convert to DTS"))]
			config.av.dtshd = ConfigSelection(choices=choice_list, default="use_hdmi_caps")
		else:
			choice_list = [("downmix", _("Downmix")), ("force_dts", _("convert to DTS")), ("use_hdmi_caps", _("controlled by HDMI")), ("multichannel", _("convert to multi-channel PCM")), ("hdmi_best", _("use best / controlled by HDMI"))]
			config.av.dtshd = ConfigSelection(choices=choice_list, default="downmix")
		config.av.dtshd.addNotifier(setDTSHD)

	if SystemInfo["CanWMAPRO"]:
		def setWMAPRO(configElement):
			with open("/proc/stb/audio/wmapro", "w") as f:
				f.write(configElement.value)
		choice_list = [("downmix",  _("Downmix")), ("passthrough", _("Passthrough")), ("multichannel",  _("convert to multi-channel PCM")), ("hdmi_best",  _("use best / controlled by HDMI"))]
		config.av.wmapro = ConfigSelection(choices = choice_list, default = "downmix")
		config.av.wmapro.addNotifier(setWMAPRO)

	if SystemInfo["CanDownmixAAC"]:
		def setAACDownmix(configElement):
			with open("/proc/stb/audio/aac", "w") as f:
				if SystemInfo["DreamBoxAudio"]:
					f.write(configElement.value)
				else:
					f.write(configElement.value and "downmix" or "passthrough")
		if SystemInfo["DreamBoxAudio"]:
			choice_list = [("downmix", _("Downmix")), ("passthrough", _("Passthrough")), ("multichannel", _("convert to multi-channel PCM")), ("hdmi_best", _("use best / controlled by HDMI"))]
			config.av.downmix_aac = ConfigSelection(choices=choice_list, default="downmix")
		else:
			config.av.downmix_aac = ConfigYesNo(default=True)
		config.av.downmix_aac.addNotifier(setAACDownmix)

	if fileExists("/proc/stb/video/alpha"):
		f = open("/proc/stb/video/alpha", "r")
		SystemInfo["CanChangeOsdAlpha"] = f and True or False
		f.close()
	else:
		SystemInfo["CanChangeOsdAlpha"] = False

	if SystemInfo["CanChangeOsdAlpha"]:
		def setAlpha(config):
			f = open("/proc/stb/video/alpha", "w")
			f.write(str(config.value))
			f.close()
		config.av.osd_alpha = ConfigSlider(default=255, limits=(0, 255))
		config.av.osd_alpha.addNotifier(setAlpha)

	if os.path.exists("/proc/stb/vmpeg/0/pep_scaler_sharpness"):
		def setScaler_sharpness(config):
			myval = int(config.value)
			try:
				print "--> setting scaler_sharpness to: %0.8X" % myval
				f = open("/proc/stb/vmpeg/0/pep_scaler_sharpness", "w")
				f.write("%0.8X" % myval)
				f.close()
			except IOError:
				print "couldn't write pep_scaler_sharpness"

			if fileExists("/proc/stb/vmpeg/0/pep_apply"):
				try:
					f = open("/proc/stb/vmpeg/0/pep_apply", "w")
					f.write("1")
					f.close()
				except IOError:
					print "couldn't write pep_apply"

		config.av.scaler_sharpness = ConfigSlider(default=13, limits=(0, 26))
		config.av.scaler_sharpness.addNotifier(setScaler_sharpness)
	else:
		config.av.scaler_sharpness = NoSave(ConfigNothing())

	if SystemInfo["HasMultichannelPCM"]:
		def setMultichannelPCM(configElement):
			f = open(SystemInfo["HasMultichannelPCM"], "w")
			f.write(configElement.value and "enable" or "disable")
			f.close()
		config.av.multichannel_pcm = ConfigYesNo(default=False)
		config.av.multichannel_pcm.addNotifier(setMultichannelPCM)

	if SystemInfo["HasAutoVolume"]:
		def setAutoVolume(configElement):
			f = open(SystemInfo["HasAutoVolume"], "w")
			f.write(configElement.value)
			f.close()
		config.av.autovolume = ConfigSelection(default="none", choices=[("none", _("off")), ("hdmi", "HDMI"), ("spdif", "SPDIF"), ("dac", "DAC")])
		config.av.autovolume.addNotifier(setAutoVolume)

	if SystemInfo["HasAutoVolumeLevel"]:
		def setAutoVolumeLevel(configElement):
			f = open(SystemInfo["HasAutoVolumeLevel"], "w")
			f.write(configElement.value and "enabled" or "disabled")
			f.close()
		config.av.autovolumelevel = ConfigYesNo(default=False)
		config.av.autovolumelevel.addNotifier(setAutoVolumeLevel)

	if SystemInfo["Has3DSurround"]:
		def set3DSurround(configElement):
			f = open(SystemInfo["Has3DSurround"], "w")
			f.write(configElement.value)
			f.close()
		config.av.surround_3d = ConfigSelection(default="none", choices=[("none", _("off")), ("hdmi", "HDMI"), ("spdif", "SPDIF"), ("dac", "DAC")])
		config.av.surround_3d.addNotifier(set3DSurround)

	if SystemInfo["Has3DSpeaker"]:
		def set3DSpeaker(configElement):
			f = open(SystemInfo["Has3DSpeaker"], "w")
			f.write(configElement.value)
			f.close()
		config.av.speaker_3d = ConfigSelection(default="center", choices=[("center", _("center")), ("wide", _("wide")), ("extrawide", _("extra wide"))])
		config.av.speaker_3d.addNotifier(set3DSpeaker)

	if SystemInfo["Has3DSurroundSpeaker"]:
		def set3DSurroundSpeaker(configElement):
			f = open(SystemInfo["Has3DSurroundSpeaker"], "w")
			f.write(configElement.value)
			f.close()
		config.av.surround_3d_speaker = ConfigSelection(default="disabled", choices=[("disabled", _("off")), ("center", _("center")), ("wide", _("wide")), ("extrawide", _("extra wide"))])
		config.av.surround_3d_speaker.addNotifier(set3DSurroundSpeaker)

	if SystemInfo["Has3DSurroundSoftLimiter"]:
		def set3DSurroundSoftLimiter(configElement):
			f = open(SystemInfo["Has3DSurroundSoftLimiter"], "w")
			f.write(configElement.value and "enabled" or "disabled")
			f.close()
		config.av.surround_softlimiter_3d = ConfigYesNo(default=False)
		config.av.surround_softlimiter_3d.addNotifier(set3DSurroundSoftLimiter)

	if SystemInfo["HDMIAudioSource"]:
		def setHDMIAudioSource(configElement):
			f = open(SystemInfo["HDMIAudioSource"], "w")
			f.write(configElement.value)
			f.close()
		config.av.hdmi_audio_source = ConfigSelection(default="pcm", choices=[("pcm", "PCM"), ("spdif", "SPDIF")])
		config.av.hdmi_audio_source.addNotifier(setHDMIAudioSource)

	def setVolumeStepsize(configElement):
		eDVBVolumecontrol.getInstance().setVolumeSteps(int(configElement.value))
	config.av.volume_stepsize = ConfigSelectionNumber(1, 10, 1, default=5)
	config.av.volume_stepsize.addNotifier(setVolumeStepsize)
