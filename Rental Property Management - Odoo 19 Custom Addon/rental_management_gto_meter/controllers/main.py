# -*- coding: utf-8 -*-
import json
from odoo import http, fields, _
from odoo.http import request


class SmartMeterIoTController(http.Controller):

    @http.route('/api/v1/meter/iot_reading', type='json', auth='none', methods=['POST'], csrf=False)
    def receive_iot_meter_reading(self, **kwargs):
        data = request.jsonrequest or {}
        meter_code = data.get('meter_code')
        reading_val = data.get('current_reading')

        if not meter_code or reading_val is None:
            return {'status': 'error', 'message': 'Missing meter_code or current_reading'}

        meter = request.env['property.meter.reading'].sudo().search([('name', '=', meter_code)], limit=1)
        if not meter:
            return {'status': 'error', 'message': f'Meter with code {meter_code} not found'}

        meter.write({
            'current_reading': reading_val,
            'reading_date': fields.Date.today(),
        })
        return {
            'status': 'success',
            'message': f'Meter reading updated for {meter_code}',
            'current_reading': reading_val,
        }
