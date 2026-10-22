package com.pixo.app

import android.Manifest
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import com.pixo.app.avatar.PixoRive
import com.pixo.app.ui.PixoApp

class MainActivity : ComponentActivity() {
    private val askMicrophone = registerForActivityResult(ActivityResultContracts.RequestPermission()) {
        // Without the microphone, `listen` answers "heard nothing" and the session still runs
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        PixoRive.init(this)
        if (savedInstanceState == null) askMicrophone.launch(Manifest.permission.RECORD_AUDIO)
        enableEdgeToEdge()
        setContent { PixoApp() }
    }
}
