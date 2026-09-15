-keep class com.google.mediapipe.** { *; }
-keep class com.google.protobuf.** { *; }
-keepclasseswithmembers class * {
    native <methods>;
}
-dontwarn com.google.mediapipe.proto.CalculatorProfileProto$CalculatorProfile
-dontwarn com.google.mediapipe.proto.GraphTemplateProto$CalculatorGraphTemplate
