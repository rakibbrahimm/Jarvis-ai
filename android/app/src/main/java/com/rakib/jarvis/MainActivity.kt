package com.rakib.jarvis

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)

        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.mediaPlaybackRequiresUserGesture = false

        webView.webViewClient = WebViewClient()
        webView.webChromeClient = WebChromeClient()

        webView.addJavascriptInterface(
            JarvisAndroidBridge(),
            "Android"
        )

        setContentView(webView)

        webView.loadUrl("file:///android_asset/index.html")

        requestCameraPermission()
    }

    private fun requestCameraPermission() {

        if (
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.CAMERA
            ) != PackageManager.PERMISSION_GRANTED
        ) {

            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.CAMERA),
                100
            )
        }
    }

    inner class JarvisAndroidBridge {

        @JavascriptInterface
        fun openUrl(url: String) {

            try {

                val intent = Intent(
                    Intent.ACTION_VIEW,
                    Uri.parse(url)
                )

                startActivity(intent)

            } catch (_: Exception) {
            }
        }

        @JavascriptInterface
        fun getDeviceName(): String {
            return android.os.Build.MODEL
        }

        @JavascriptInterface
        fun vibrate() {

            val vibrator =
                getSystemService(VIBRATOR_SERVICE)
                    as android.os.Vibrator

            vibrator.vibrate(
                android.os.VibrationEffect.createOneShot(
                    100,
                    android.os.VibrationEffect.DEFAULT_AMPLITUDE
                )
            )
        }
    }

    override fun onBackPressed() {

        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
