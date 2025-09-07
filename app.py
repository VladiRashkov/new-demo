from flask import Flask, render_template
from apps.forecast.routes import forecast_bp
from apps.noise.routes import noise_bp
from apps.vibration.routes import vibration_bp

app = Flask(__name__)
app.register_blueprint(forecast_bp)
app.register_blueprint(noise_bp)
app.register_blueprint(vibration_bp)


@app.route('/')
def base():
    return render_template('base.html')

# app.route('/logout')
# def logout():
#     return render_template()

if __name__ == '__main__':
    app.run(debug=True)
